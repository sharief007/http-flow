const port = chrome.runtime.connectNative('com.my_company.my_app');

port.onMessage.addListener((msg) => {
  console.log('Received message from native app:', msg);
});

port.onDisconnect.addListener(() => {
  console.log('Disconnected from native app');
});

// Example of sending a message to the native app
// port.postMessage({ text: 'Hello from extension' });
