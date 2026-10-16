'use strict';
const deny=()=>{throw new Error('Offline acceptance forbids actual network');};
require('net').Socket.prototype.connect=deny;
require('tls').connect=deny;
require('dgram').Socket.prototype.send=deny;
require('dns').lookup=deny;
