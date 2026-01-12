
class RecorderProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input.length > 0) {
            const channelData = input[0];
            if (channelData) {
                // Send raw float32 data to the main thread
                this.port.postMessage(channelData);
            }
        }
        return true; // Keep processor alive
    }
}

registerProcessor('recorder-processor', RecorderProcessor);
