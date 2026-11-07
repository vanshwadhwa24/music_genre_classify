/**
 * AudioStreamer manages browser microphone capture, Web Audio API analysis,
 * and periodic audio window collection for live CNN inference.
 */

export interface AudioStreamerCallbacks {
  onAudioChunk: (blob: Blob) => void
  onError: (error: string) => void
  onPermissionDenied?: () => void
}

export class AudioStreamer {
  private mediaStream: MediaStream | null = null
  private audioContext: AudioContext | null = null
  private analyserNode: AnalyserNode | null = null
  private sourceNode: MediaStreamAudioSourceNode | null = null
  private mediaRecorder: MediaRecorder | null = null
  private sliceIntervalId: number | null = null
  private isListening: boolean = false
  private callbacks: AudioStreamerCallbacks

  // Rolling window parameters
  private readonly windowDurationMs: number = 2500 // 2.5 seconds per inference slice

  constructor(callbacks: AudioStreamerCallbacks) {
    this.callbacks = callbacks
  }

  async start(): Promise<boolean> {
    if (this.isListening) return true

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.callbacks.onError('Microphone input is not supported by your browser or environment.')
      return false
    }

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      })
    } catch (err: unknown) {
      const error = err as Error
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        if (this.callbacks.onPermissionDenied) {
          this.callbacks.onPermissionDenied()
        } else {
          this.callbacks.onError('Microphone access was denied. Please allow microphone permissions in browser settings.')
        }
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        this.callbacks.onError('No microphone hardware was detected on your system.')
      } else {
        this.callbacks.onError(`Could not initialize microphone: ${error.message}`)
      }
      return false
    }

    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      this.audioContext = new AudioCtx()
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      this.analyserNode = this.audioContext.createAnalyser()
      this.analyserNode.fftSize = 512
      this.analyserNode.smoothingTimeConstant = 0.82

      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream)
      this.sourceNode.connect(this.analyserNode)

      // Start rolling window MediaRecorder
      this.startRollingRecorder()

      this.isListening = true
      return true
    } catch (err: unknown) {
      this.stop()
      this.callbacks.onError(`Audio processing error: ${(err as Error).message}`)
      return false
    }
  }

  private startRollingRecorder(): void {
    if (!this.mediaStream) return

    // Find supported mime type
    let mimeType = 'audio/webm'
    if (!MediaRecorder.isTypeSupported('audio/webm')) {
      if (MediaRecorder.isTypeSupported('audio/ogg; codecs=opus')) {
        mimeType = 'audio/ogg; codecs=opus'
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4'
      } else {
        mimeType = '' // Default browser codec
      }
    }

    let recordedChunks: Blob[] = []

    const startSession = () => {
      if (!this.mediaStream || !this.mediaStream.active) return
      try {
        const recorder = mimeType ? new MediaRecorder(this.mediaStream, { mimeType }) : new MediaRecorder(this.mediaStream)
        this.mediaRecorder = recorder

        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            recordedChunks.push(e.data)
          }
        }

        recorder.onstop = () => {
          if (recordedChunks.length > 0) {
            const finalBlob = new Blob(recordedChunks, { type: mimeType || 'audio/webm' })
            recordedChunks = []
            this.callbacks.onAudioChunk(finalBlob)
          }
        }

        recorder.start()

        // Stop recorder after window duration to trigger onstop, then immediately restart
        this.sliceIntervalId = window.setTimeout(() => {
          if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop()
          }
          if (this.isListening) {
            startSession()
          }
        }, this.windowDurationMs)
      } catch (err) {
        console.warn('Error during MediaRecorder chunk generation:', err)
      }
    }

    startSession()
  }

  getFrequencyData(targetArray: Uint8Array<ArrayBuffer>): void {
    if (this.analyserNode) {
      this.analyserNode.getByteFrequencyData(targetArray)
    }
  }

  getTimeDomainData(targetArray: Uint8Array<ArrayBuffer>): void {
    if (this.analyserNode) {
      this.analyserNode.getByteTimeDomainData(targetArray)
    }
  }

  getAnalyser(): AnalyserNode | null {
    return this.analyserNode
  }

  stop(): void {
    this.isListening = false

    if (this.sliceIntervalId) {
      window.clearTimeout(this.sliceIntervalId)
      this.sliceIntervalId = null
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop()
      } catch {
        // ignore
      }
      this.mediaRecorder = null
    }

    if (this.sourceNode) {
      try {
        this.sourceNode.disconnect()
      } catch {
        // ignore
      }
      this.sourceNode = null
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close()
      } catch {
        // ignore
      }
      this.audioContext = null
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop())
      this.mediaStream = null
    }
  }

  isActive(): boolean {
    return this.isListening
  }
}
