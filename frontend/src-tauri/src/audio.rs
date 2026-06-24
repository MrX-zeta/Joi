use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{self, RecvTimeoutError};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::SampleFormat;
use tauri::{AppHandle, Emitter, State};

// --- Parámetros del VAD (ajusta a tu micro/ambiente) ---
const RMS_THRESHOLD: f32 = 0.015; // súbelo si capta ruido, bájalo si no te oye
const SPEECH_START_MS: u32 = 150; // voz sostenida para arrancar
const SILENCE_END_MS: u32 = 800; // silencio para cerrar la frase
const MIN_UTTERANCE_MS: u32 = 300; // descarta blips de ruido
const PREROLL_MS: u32 = 300; // audio previo para no cortar la 1ª sílaba
const TARGET_RATE: u32 = 16000;

#[derive(Default)]
pub struct AudioState {
    stop: Arc<AtomicBool>,
    running: Mutex<bool>,
}

#[tauri::command]
pub fn start_listening(app: AppHandle, state: State<AudioState>) -> Result<(), String> {
    let mut running = state.running.lock().unwrap();
    if *running {
        return Ok(());
    }
    state.stop.store(false, Ordering::Relaxed);
    let stop = state.stop.clone();
    thread::spawn(move || {
        if let Err(e) = capture_loop(app, stop) {
            eprintln!("[audio] error: {e}");
        }
    });
    *running = true;
    Ok(())
}

#[tauri::command]
pub fn stop_listening(state: State<AudioState>) -> Result<(), String> {
    state.stop.store(true, Ordering::Relaxed);
    *state.running.lock().unwrap() = false;
    Ok(())
}

fn capture_loop(app: AppHandle, stop: Arc<AtomicBool>) -> Result<(), String> {
    let host = cpal::default_host();
    let device = host
        .default_input_device()
        .ok_or("no hay micrófono por defecto")?;
    let config = device.default_input_config().map_err(|e| e.to_string())?;
    let sample_rate = config.sample_rate().0;
    let channels = config.channels() as usize;
    let sample_format = config.sample_format();
    let stream_config: cpal::StreamConfig = config.into();

    let (tx, rx) = mpsc::channel::<Vec<f32>>();
    let err_fn = |e| eprintln!("[audio] stream error: {e}");

    let stream = match sample_format {
        SampleFormat::F32 => {
            let tx = tx.clone();
            device.build_input_stream(
                &stream_config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    let _ = tx.send(downmix(data, channels));
                },
                err_fn,
                None,
            )
        }
        SampleFormat::I16 => {
            let tx = tx.clone();
            device.build_input_stream(
                &stream_config,
                move |data: &[i16], _: &cpal::InputCallbackInfo| {
                    let f: Vec<f32> = data.iter().map(|s| *s as f32 / 32768.0).collect();
                    let _ = tx.send(downmix(&f, channels));
                },
                err_fn,
                None,
            )
        }
        other => return Err(format!("formato no soportado: {other:?}")),
    }
    .map_err(|e| e.to_string())?;

    stream.play().map_err(|e| e.to_string())?;
    println!("[audio] escuchando @ {sample_rate} Hz, {channels} canal(es)");

    let mut in_speech = false;
    let mut voiced_ms = 0f32;
    let mut silence_ms = 0f32;
    let mut utterance: Vec<f32> = Vec::new();

    let preroll_cap = (sample_rate as f32 * PREROLL_MS as f32 / 1000.0) as usize;
    let mut preroll: Vec<f32> = Vec::with_capacity(preroll_cap);

    while !stop.load(Ordering::Relaxed) {
        let chunk = match rx.recv_timeout(Duration::from_millis(100)) {
            Ok(c) => c,
            Err(RecvTimeoutError::Timeout) => continue,
            Err(RecvTimeoutError::Disconnected) => break,
        };
        let chunk_ms = chunk.len() as f32 / sample_rate as f32 * 1000.0;
        let voiced = rms(&chunk) > RMS_THRESHOLD;

        if !in_speech {
            preroll.extend_from_slice(&chunk);
            if preroll.len() > preroll_cap {
                let drop = preroll.len() - preroll_cap;
                preroll.drain(0..drop);
            }
            if voiced {
                voiced_ms += chunk_ms;
                if voiced_ms >= SPEECH_START_MS as f32 {
                    in_speech = true;
                    silence_ms = 0.0;
                    utterance.clear();
                    utterance.extend_from_slice(&preroll);
                    let _ = app.emit("joi://listening", ());
                }
            } else {
                voiced_ms = 0.0;
            }
        } else {
            utterance.extend_from_slice(&chunk);
            if voiced {
                silence_ms = 0.0;
            } else {
                silence_ms += chunk_ms;
                if silence_ms >= SILENCE_END_MS as f32 {
                    let dur_ms = utterance.len() as f32 / sample_rate as f32 * 1000.0;
                    if dur_ms >= MIN_UTTERANCE_MS as f32 {
                        let audio16 = resample_to_16k(&utterance, sample_rate);
                        println!("[audio] frase: {:.1}s -> {} muestras 16k", dur_ms / 1000.0, audio16.len());
                        let _ = app.emit("joi://utterance", audio16);
                    }
                    let _ = app.emit("joi://speech-end", ());
                    in_speech = false;
                    voiced_ms = 0.0;
                    silence_ms = 0.0;
                    utterance.clear();
                    preroll.clear();
                }
            }
        }
    }

    println!("[audio] detenido");
    Ok(())
}

fn downmix(data: &[f32], channels: usize) -> Vec<f32> {
    if channels <= 1 {
        data.to_vec()
    } else {
        data.chunks(channels)
            .map(|f| f.iter().sum::<f32>() / channels as f32)
            .collect()
    }
}

fn rms(data: &[f32]) -> f32 {
    if data.is_empty() {
        return 0.0;
    }
    let sum: f32 = data.iter().map(|s| s * s).sum();
    (sum / data.len() as f32).sqrt()
}

fn resample_to_16k(input: &[f32], from: u32) -> Vec<f32> {
    if from == TARGET_RATE {
        return input.to_vec();
    }
    let ratio = TARGET_RATE as f32 / from as f32;
    let out_len = (input.len() as f32 * ratio) as usize;
    let mut out = Vec::with_capacity(out_len);
    let last = input.len().saturating_sub(1);
    for i in 0..out_len {
        let src = i as f32 / ratio;
        let idx = src as usize;
        let frac = src - idx as f32;
        let a = input[idx.min(last)];
        let b = input[(idx + 1).min(last)];
        out.push(a + (b - a) * frac);
    }
    out
}