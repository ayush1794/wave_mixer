#!/usr/bin/python

from sys import byteorder
from array import array
from struct import pack
import signal
import pyaudio
import wave
import time

THRESHOLD = 1500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 16000

class Recorder(object):
  def is_silent(self,snd_data):
      "Returns 'True' if below the 'silent' threshold"
      return max(snd_data) < THRESHOLD

  def normalize(self,snd_data):
      "Average the volume out"
      MAXIMUM = 16384
      times = float(MAXIMUM)/max(abs(i) for i in snd_data)

      r = array('h')
      for i in snd_data:
          r.append(int(i*times))
      return r

  def trim(self,snd_data):
      "Trim the blank spots at the start and end"
      def _trim(snd_data):
          snd_started = False
          r = array('h')

          for i in snd_data:
              if not snd_started and abs(i)>THRESHOLD:
                  snd_started = True
                  r.append(i)

              elif snd_started:
                  r.append(i)
          return r

    # Trim to the left
      snd_data = _trim(snd_data)

    # Trim to the right
      snd_data.reverse()
      snd_data = _trim(snd_data)
      snd_data.reverse()
      return snd_data

  def add_silence(self,snd_data, seconds):
      "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
      r = array('h', [0 for i in xrange(int(seconds*RATE))])
      r.extend(snd_data)
      r.extend([0 for i in xrange(int(seconds*RATE))])
      return r

  def record(self):
      """
      Record a word or words from the microphone and 
      return the data as an array of signed shorts.

      Normalizes the audio, trims silence from the 
      start and end, and pads with 0.5 seconds of 
      blank sound to make sure VLC et al can play 
      it without getting chopped off.
      """
      p = pyaudio.PyAudio()
      stream = p.open(format=FORMAT, channels=1, rate=RATE,
          input=True, output=True,
          frames_per_buffer=CHUNK_SIZE)

      num_silent = 0
      snd_started = False

      r = array('h')

      while 1:
        # little endian, signed short
          snd_data = array('h', stream.read(CHUNK_SIZE))
          if byteorder == 'big':
              snd_data.byteswap()
          r.extend(snd_data)

          silent = self.is_silent(snd_data)

          if silent and snd_started:
              num_silent += 1
          elif not silent and not snd_started:
              snd_started = True

          if snd_started and num_silent > 30:
              break

      sample_width = p.get_sample_size(FORMAT)
      stream.stop_stream()
      stream.close()
      p.terminate()

      r = self.normalize(r)
      r = self.trim(r)
      r = self.add_silence(r, 0.5)
      return sample_width, r

  def record_to_file(self):
      "Records from the microphone and outputs the resulting data to 'path'"
      pa="WAV_"+time.asctime()+".wav"
      pa=pa.replace(' ','_')
      sample_width, data = self.record()
      data = pack('<' + ('h'*len(data)), *data)

      wf = wave.open(pa, 'wb')
      wf.setnchannels(1)
      wf.setsampwidth(sample_width)
      wf.setframerate(RATE)
      wf.writeframes(data)
      wf.close()
      print "DONE"
