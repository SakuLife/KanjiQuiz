# voicevox_handler.py
import os
import time
import subprocess
import requests
import signal

class VoicevoxHandler:
    def __init__(self, engine_path):
        self.engine_path = engine_path
        self.process = None
        self.base_url = "http://127.0.0.1:50021"

    def start_engine(self):
        # VOICEVOXエンジンの存在確認
        if not os.path.exists(self.engine_path):
            print("ERROR: VOICEVOX engine not found!")
            print(f"ERROR: Missing path: {self.engine_path}")
            print("ERROR: Install VOICEVOX and update the path in core/app.py")
            raise Exception(f"VOICEVOX engine not found at {self.engine_path}")

        # 他のプロセスでVOICEVOXが起動していないかチェック
        try:
            response = requests.get(self.base_url, timeout=2)
            if response.status_code == 200:
                # 他のプロセスで既に起動している場合
                print("ERROR: VOICEVOX engine is already running on another process/system!")
                print("ERROR: Terminating all VOICEVOX processes and restarting...")

                # 全てのVOICEVOXプロセスを強制終了
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "run.exe"],
                                 capture_output=True, check=False)
                    subprocess.run(["taskkill", "/F", "/IM", "VOICEVOX.exe"],
                                 capture_output=True, check=False)
                    subprocess.run(["taskkill", "/F", "/IM", "VoicevoxEngine.exe"],
                                 capture_output=True, check=False)
                    time.sleep(3)  # プロセス終了を待つ
                    print("INFO: Terminated existing VOICEVOX processes")
                except Exception as e:
                    print(f"WARNING: Failed to terminate VOICEVOX processes: {e}")

                # ポートが空いているか確認
                try:
                    response = requests.get(self.base_url, timeout=1)
                    if response.status_code == 200:
                        raise Exception("VOICEVOX port still occupied after termination")
                except requests.exceptions.RequestException:
                    print("INFO: VOICEVOX port is now free")
        except requests.exceptions.RequestException:
            pass  # エンジンが起動していない（正常）

        if self.process and self.process.poll() is None:
            # 自分のプロセスのエンジンが動いているかテスト
            try:
                response = requests.get(self.base_url, timeout=2)
                if response.status_code == 200:
                    print("INFO: VOICEVOX engine is already running and responsive.")
                    return True
                else:
                    print("WARNING: VOICEVOX engine process exists but not responsive - restarting...")
                    self.stop_engine()
            except requests.exceptions.RequestException:
                print("WARNING: VOICEVOX engine process exists but not responsive - restarting...")
                self.stop_engine()

        print("INFO: Starting VOICEVOX engine...")
        try:
            self.process = subprocess.Popen(self.engine_path, creationflags=subprocess.CREATE_NO_WINDOW)
            for attempt in range(30):  # 15回 -> 30回に増加
                try:
                    response = requests.get(self.base_url, timeout=3)  # 2秒 -> 3秒に増加
                    if response.status_code == 200:
                        print("INFO: VOICEVOX engine started successfully.")
                        # スピーカー一覧取得でさらに確認
                        try:
                            speakers_response = requests.get(f"{self.base_url}/speakers", timeout=10)  # 5秒 -> 10秒に増加
                            if speakers_response.status_code == 200:
                                print("INFO: VOICEVOX engine fully operational.")
                                return True
                            else:
                                raise Exception(f"Speakers API returned status {speakers_response.status_code}")
                        except Exception as e:
                            print(f"ERROR: VOICEVOX engine not fully operational: {e}")
                            if self.process:
                                self.process.terminate()
                                self.process = None
                            raise Exception("VOICEVOX engine startup verification failed")
                        return True
                except requests.exceptions.RequestException:
                    if attempt < 29:  # 14 -> 29に変更
                        time.sleep(3)  # 2秒 -> 3秒に増加
            print("ERROR: VOICEVOX engine did not start within the time limit")
            if self.process:
                self.process.terminate()
                self.process = None
            raise Exception("VOICEVOX engine startup timeout - cannot proceed without audio")
        except Exception as e:
            print(f"ERROR: Failed to start VOICEVOX engine: {str(e)}")
            if self.process:
                self.process.terminate()
                self.process = None
            raise Exception(f"VOICEVOX engine startup failed: {str(e)}")

    def stop_engine(self):
        if self.process and self.process.poll() is None:
            print("INFO: Stopping VOICEVOX engine...")
            self.process.send_signal(signal.CTRL_C_EVENT)
            try:
                self.process.wait(timeout=5)
                print("INFO: VOICEVOX engine stopped gracefully.")
            except subprocess.TimeoutExpired:
                print("WARNING: VOICEVOX did not stop gracefully, killing the process.")
                self.process.kill()
            self.process = None

    def generate_voice(self, text, output_path, speed=1.3, speaker=13):
        """VOICEVOX APIを使って音声を生成する (モックモード対応)"""
        print(f"INFO: Generating voice for text length: {len(text)} chars (Speaker: {speaker}, Speed: {speed})")
        
        # VOICEVOXエンジンが利用できない場合はエラーで終了
        is_engine_available = self._check_engine_availability()
        if not is_engine_available:
            print(f"ERROR: VOICEVOX engine not available for audio generation!")
            print(f"ERROR: Cannot proceed without functional VOICEVOX engine!")
            raise Exception("VOICEVOX engine not available - cannot generate audio")
        
        # 通常のVOICEVOX処理
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            query_payload = {"text": text, "speaker": speaker}
            response_query = requests.post(f"{self.base_url}/audio_query", params=query_payload, timeout=20)
            response_query.raise_for_status()
            audio_query = response_query.json()
            audio_query["speedScale"] = speed
            
            synthesis_payload = {"speaker": speaker}
            response_synth = requests.post(
                f"{self.base_url}/synthesis",
                params=synthesis_payload,
                json=audio_query,
                timeout=120 
            )
            response_synth.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response_synth.content)

            return True
        except Exception as e:
            print(f"ERROR: Voice generation failed: {e}")
            print(f"ERROR: Cannot proceed without functional audio generation!")
            raise Exception(f"VOICEVOX voice generation failed: {str(e)}")
    
    def _check_engine_availability(self):
        """VOICEVOXエンジンが利用可能かチェックする"""
        if not os.path.exists(self.engine_path):
            return False
        
        if not self.process or self.process.poll() is not None:
            return False
            
        try:
            response = requests.get(self.base_url, timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

