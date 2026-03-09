"""
VTube Studio API Integration
Controls Live2D avatar through VTube Studio
"""
import json
import asyncio
import websockets
import threading
import time
from typing import Optional, Dict

class VTubeStudioAPI:
    """VTube Studio WebSocket API client"""
    
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.connected = False
        self.authenticated = False
        self.plugin_name = "KD6 AI Companion"
        self.plugin_developer = "KD6"
        self.auth_token = None
        
        # API settings
        self.host = config.get('vtube_studio', {}).get('host', 'localhost')
        self.port = config.get('vtube_studio', {}).get('port', 8001)
        self.uri = f"ws://{self.host}:{self.port}"
        
        # Current state
        self.current_model = None
        self.available_hotkeys = []
        
        # Message queue for sending
        self.send_queue = asyncio.Queue()
        
        # Start connection in background
        self.running = True
        self.loop = None
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
    
    def _run_async_loop(self):
        """Run async event loop in separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Create queue in this loop
        self.send_queue = asyncio.Queue()
        
        self.loop.run_until_complete(self._connect_and_maintain())
    
    async def _connect_and_maintain(self):
        """Connect and maintain connection"""
        while self.running:
            try:
                print(f"🔌 Connecting to VTube Studio at {self.uri}...")
                async with websockets.connect(
                    self.uri,
                    ping_interval=15,
                    ping_timeout=10,
                    close_timeout=5
                ) as websocket:
                    self.ws = websocket
                    self.connected = True
                    print("✓ Connected to VTube Studio")
                    
                    # Authenticate
                    await self._authenticate()
                    
                    if not self.authenticated:
                        print("⚠ Authentication failed - check VTube Studio for approval prompt")
                        self.connected = False
                        await asyncio.sleep(5)
                        continue
                    
                    # Get current model info
                    await self._get_current_model()
                    
                    # Get available hotkeys
                    await self._get_hotkeys()
                    
                    # Get available parameters (for debugging)
                    await self._get_parameters()
                    
                    # Process send queue and keep connection alive
                    while self.running and self.connected:
                        try:
                            # Check for messages to send
                            message = await asyncio.wait_for(self.send_queue.get(), timeout=1.0)
                            await self.ws.send(json.dumps(message))
                        except asyncio.TimeoutError:
                            # No message to send, just continue to keep loop alive
                            pass
                        except websockets.exceptions.ConnectionClosed:
                            print("⚠ Connection closed by VTube Studio")
                            break
                        except Exception as e:
                            print(f"✗ Send error: {e}")
                            break
                        
            except websockets.exceptions.ConnectionClosed as e:
                print(f"⚠ VTube Studio connection closed: {e}")
                self.connected = False
                self.authenticated = False
                await asyncio.sleep(3)
            except Exception as e:
                print(f"✗ VTube Studio connection error: {e}")
                self.connected = False
                self.authenticated = False
                await asyncio.sleep(5)  # Wait before reconnecting
    
    def _queue_message(self, message_type: str, data: Dict = None):
        """Queue a message to send (fire and forget)"""
        if not self.connected:
            return
        
        if not self.authenticated:
            return
        
        if not self.loop:
            return
        
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(int(time.time() * 1000)),
            "messageType": message_type
        }
        
        if data:
            request["data"] = data
        
        # Add to queue
        try:
            asyncio.run_coroutine_threadsafe(
                self.send_queue.put(request),
                self.loop
            )
        except Exception as e:
            print(f"✗ Queue error: {e}")
    
    async def _authenticate(self):
        """Authenticate with VTube Studio"""
        try:
            # If we already have a token, try to use it
            if self.auth_token:
                print("🔑 Using saved authentication token")
                auth_request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "auth",
                    "messageType": "AuthenticationRequest",
                    "data": {
                        "pluginName": self.plugin_name,
                        "pluginDeveloper": self.plugin_developer,
                        "authenticationToken": self.auth_token
                    }
                }
                
                await self.ws.send(json.dumps(auth_request))
                auth_response_str = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                auth_response = json.loads(auth_response_str)
                
                if auth_response.get('data', {}).get('authenticated'):
                    self.authenticated = True
                    print("✓ Authenticated with saved token")
                    return
                else:
                    print("⚠ Saved token invalid, requesting new one")
                    self.auth_token = None
            
            # Request new authentication token
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "auth_token",
                "messageType": "AuthenticationTokenRequest",
                "data": {
                    "pluginName": self.plugin_name,
                    "pluginDeveloper": self.plugin_developer
                }
            }
            
            await self.ws.send(json.dumps(request))
            response_str = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            response = json.loads(response_str)
            
            if 'data' in response and 'authenticationToken' in response['data']:
                self.auth_token = response['data']['authenticationToken']
                print(f"✓ Got new authentication token")
                
                # Authenticate with new token
                auth_request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "auth",
                    "messageType": "AuthenticationRequest",
                    "data": {
                        "pluginName": self.plugin_name,
                        "pluginDeveloper": self.plugin_developer,
                        "authenticationToken": self.auth_token
                    }
                }
                
                print("⏳ Waiting for VTube Studio approval (check for popup)...")
                await self.ws.send(json.dumps(auth_request))
                auth_response_str = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                auth_response = json.loads(auth_response_str)
                
                if auth_response.get('data', {}).get('authenticated'):
                    self.authenticated = True
                    print("✓ Authenticated with VTube Studio")
                else:
                    print("✗ Authentication rejected")
                    print("  → Check VTube Studio for approval popup")
            else:
                print("✗ Failed to get authentication token")
                if 'data' in response:
                    error_msg = response['data'].get('message', 'Unknown error')
                    print(f"  → {error_msg}")
        except asyncio.TimeoutError:
            print("✗ Authentication timeout")
            print("  → Make sure VTube Studio API is enabled")
            print("  → Settings → Broadcast Icon → Start API = ON")
        except Exception as e:
            print(f"✗ Authentication error: {e}")
    
    async def _get_current_model(self):
        """Get current loaded model info"""
        try:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "model_info",
                "messageType": "CurrentModelRequest"
            }
            
            await self.ws.send(json.dumps(request))
            response_str = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
            response = json.loads(response_str)
            
            if 'data' in response:
                self.current_model = response['data']
                model_name = self.current_model.get('modelName', 'Unknown')
                print(f"✓ Current model: {model_name}")
        except Exception as e:
            print(f"✗ Get model error: {e}")
    
    async def _get_hotkeys(self):
        """Get available hotkeys"""
        try:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "hotkeys",
                "messageType": "HotkeysInCurrentModelRequest"
            }
            
            await self.ws.send(json.dumps(request))
            response_str = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
            response = json.loads(response_str)
            
            if 'data' in response:
                self.available_hotkeys = response['data'].get('availableHotkeys', [])
                print(f"✓ Found {len(self.available_hotkeys)} hotkeys")
        except Exception as e:
            print(f"✗ Get hotkeys error: {e}")
    
    async def _get_parameters(self):
        """Get available parameters for debugging"""
        try:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "params",
                "messageType": "InputParameterListRequest"
            }
            
            await self.ws.send(json.dumps(request))
            response_str = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
            response = json.loads(response_str)
            
            if 'data' in response:
                params = response['data'].get('defaultParameters', [])
                mouth_params = [p for p in params if 'mouth' in p.get('name', '').lower()]
                if mouth_params:
                    print(f"✓ Found mouth parameters: {[p['name'] for p in mouth_params]}")
                else:
                    print("⚠ No mouth parameters found")
        except Exception as e:
            print(f"✗ Get parameters error: {e}")
    
    def set_parameter(self, parameter_name: str, value: float):
        """Set Live2D parameter value"""
        if not self.connected or not self.authenticated:
            return
        
        self._queue_message("InjectParameterDataRequest", {
            "parameterValues": [
                {
                    "id": parameter_name,
                    "value": value
                }
            ]
        })
    
    def trigger_hotkey(self, hotkey_id: str):
        """Trigger a hotkey/expression"""
        if not self.connected or not self.authenticated:
            return
        
        self._queue_message("HotkeyTriggerRequest", {
            "hotkeyID": hotkey_id
        })
    
    def set_mouth_open(self, value: float):
        """Set mouth open parameter (0.0 to 1.0)"""
        # Ariu model uses "MouthOpen" parameter
        self.set_parameter("MouthOpen", value)
    
    def set_emotion(self, emotion: str):
        """Set emotion via hotkeys"""
        # Map emotions to common hotkey names
        emotion_hotkeys = {
            'happy': 'Happy',
            'sad': 'Sad',
            'angry': 'Angry',
            'surprised': 'Surprised',
            'neutral': 'Neutral'
        }
        
        hotkey_name = emotion_hotkeys.get(emotion.lower())
        if hotkey_name:
            # Find hotkey ID
            for hotkey in self.available_hotkeys:
                if hotkey_name.lower() in hotkey.get('name', '').lower():
                    self.trigger_hotkey(hotkey['hotkeyID'])
                    break
    
    def cleanup(self):
        """Cleanup connection"""
        self.running = False
        self.connected = False
        if self.loop:
            self.loop.stop()
