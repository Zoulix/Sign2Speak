#!/usr/bin/env python3
"""
Wrapper pour le moteur de traduction de la langue des signes
Intégré au système Sign2Speak
"""

import cv2
import mediapipe as mp
import numpy as np
try:
    from ai_edge_litert.interpreter import Interpreter as TFLiteInterpreter
except ImportError:
    import tflite_runtime.interpreter as tflite
    TFLiteInterpreter = tflite.Interpreter
import json
from llama_cpp import Llama
import subprocess
import os
import threading
from typing import Optional
from pathlib import Path
import platform
import time


class SentenceGenerator:
    """Classe pour la traduction par le LLM"""
    def __init__(self, model_path="moteur_trad_pi/Model/qwen2.5-0.5b-instruct-q4_k_m.gguf"):
        base_path = Path(__file__).parent.parent.parent
        full_model_path = base_path / model_path
        
        print(f"Chargement du modèle LLM depuis: {full_model_path}")
        
        if not full_model_path.exists():
            raise FileNotFoundError(f"Modèle LLM non trouvé: {full_model_path}")
        
        self.llm = Llama(
            model_path=str(full_model_path),
            n_ctx=512,
            n_threads=4,
            verbose=False
        )

    def translate(self, glosses_input):
        prompt = f"""<|im_start|>system
        You are a professional Sign Language interpreter. 
        Your task is to convert American Sign Language glosses (keywords) into a natural, grammatically correct, and polite French sentence. 
        Your task will be to use keywords (subject, verb, object) to form syntactically correct French sentences.
        Rules:
        - THE OUTPUT MUST BE ONLY IN FRENCH.
        - Do not add comments.
        - If the input is a single word or expression, the output must be its literal translation into French.
        - Fix grammar, articles (le, la, les) and verb conjugation.
        - Don't stray too far from the general meaning of the keywords.
        - You should always check that your output is syntactically and semantically correct
        The expression ["thankyou"] outputs "Merci beaucoup".
        Examples:
        Input: ['thankyou']
        Output: Merci beaucoup.
        Input: ['me', 'drink', 'water']
        Output: Je bois de l'eau.
        Input: ['mom', 'like', 'apple']
        Output: Maman aime les pommes.
        Input: ['weus', 'drink', 'water']
        Output: Nous buvons de l'eau.
        Input: ['hesheit', 'taste']
        Output: Il goûte. 
        Input: ['thankyou']
        Output: Merci.
        Input: ['boy', 'read', 'milk', 'book']
        Output: Le garçon lit un livre.
        Input: ['taste']
        Output: Goûter.
        </system>

        Input: {glosses_input}
        Output:
        
        """
        output = self.llm(
            prompt,
            max_tokens=80,
            stop=["</s>", "\n", "Input:"],
            temperature=0.1,
            repeat_penalty=1.2
        )
        return output['choices'][0]['text'].strip()


class TextToSpeech:
    """Classe pour la sortie Audio avec Piper (adaptée pour Raspberry Pi et PC avec Bluetooth)"""
    def __init__(self, piper_folder="moteur_trad_pi/piper", model_name="fr_FR-upmc-medium.onnx", bt_sink=None):
        base_path = Path(__file__).parent.parent.parent
        self.piper_bin = base_path / piper_folder / "piper"
        self.model_path = base_path / piper_folder / model_name
        self.sample_rate = "22050"
        self.bt_sink = bt_sink  # Nom du sink PipeWire Bluetooth (ex: bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink)
        
        print(f"Chemin Piper: {self.piper_bin}")
        print(f"Chemin modèle TTS: {self.model_path}")
        
        if not self.piper_bin.exists():
            raise FileNotFoundError(f"Exécutable Piper non trouvé: {self.piper_bin}")
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modèle TTS non trouvé: {self.model_path}")

    def set_sink(self, sink_name):
        """Met à jour le sink audio cible."""
        self.bt_sink = sink_name
        print(f"🔊 Sink audio défini : {sink_name}")

    def _build_play_command(self):
        """Construit la commande de lecture audio selon la plateforme et le sink Bluetooth."""
        # Détecte si on tourne sur Raspberry Pi
        is_pi = "aarch64" in platform.machine() or "armv" in platform.machine()
        
        if is_pi:
            # pw-play supporte --raw sur le Pi
            target = f'--target="{self.bt_sink}"' if self.bt_sink else ''
            return (
                f'pw-play --raw --rate={self.sample_rate} '
                f'--channels=1 --format=s16 {target} -'
            )
        else:
            # paplay sur PC Ubuntu
            device = f'--device="{self.bt_sink}"' if self.bt_sink else ''
            return (
                f'paplay --raw --rate={self.sample_rate} '
                f'--channels=1 --format=s16le {device}'
            )

    def speak(self, text):
        """Méthode principale pour parler sans bloquer le système."""
        if text:
            # Nettoyage du texte pour éviter les injections de commandes shell
            safe_text = text.replace('"', '')
            
            # Commande pipeline pour envoyer le flux audio vers le lecteur approprié
            play_cmd = self._build_play_command()
            command = (
                f'echo "{safe_text}" | {self.piper_bin} --model {self.model_path} '
                f'--output_raw | {play_cmd}'
            )

            def run():
                start_time = time.time()
                try:
                    subprocess.run(command, shell=True, check=True, stderr=subprocess.DEVNULL)
                    audio_routing_time = time.time() - start_time
                    print(f"⏱️ Temps Routage Audio Complet (génération + lecture) : {audio_routing_time:.3f}s")
                except subprocess.CalledProcessError:
                    print("Erreur : Vérifiez que le périphérique audio est connecté.")

            threading.Thread(target=run, daemon=True).start()


class TranslationEngine:
    """Moteur de Traduction Principal"""
    def __init__(self, camera_index: int = 2, bt_sink: Optional[str] = None):
        self.camera_index = camera_index
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.cap = None
        self.current_frame = None
        self.current_text = ""
        self.current_status = ""
        self.current_sentence = ""
        self.bt_sink = bt_sink  # Sink Bluetooth pour le routage audio
        
        # Initialisation des modèles et outils
        self.init_models()
        self.init_parameters()
        self.init_state()
        
        # Initialisation des générateurs LLM et TTS au démarrage pour éviter le délai lors de la première traduction
        print("Initialisation des modèles LLM et TTS...")
        self.sentence_generator = SentenceGenerator()
        self.text_to_speech = TextToSpeech(bt_sink=self.bt_sink)
        print("Modèles LLM et TTS chargés.")

    def init_models(self):
        """Initialise les modèles ML"""
        base_path = Path(__file__).parent.parent.parent
        
        # MediaPipe
        self.mp_holistic = mp.solutions.holistic
        
        # TFLite
        sign_map_path = base_path / "moteur_trad_pi" / "sign_to_prediction_index_map.json"
        model_path = base_path / "moteur_trad_pi" / "Model" / "model.tflite"
        
        print(f"Chargement du fichier de mapping: {sign_map_path}")
        print(f"Chargement du modèle TFLite: {model_path}")
        
        if not sign_map_path.exists():
            raise FileNotFoundError(f"Fichier de mapping non trouvé: {sign_map_path}")
        if not model_path.exists():
            raise FileNotFoundError(f"Modèle TFLite non trouvé: {model_path}")
        
        with open(sign_map_path, 'r') as f:
            s2p_map = json.load(f)
        self.actions = {v: k for k, v in s2p_map.items()}
        self.interpreter = TFLiteInterpreter(model_path=str(model_path))
        self.interpreter.allocate_tensors()
        self.prediction_fn = self.interpreter.get_signature_runner("serving_default")

    def init_parameters(self):
        """Initialise les paramètres de stabilité"""
        self.MAX_FRAMES = 30
        self.THRESHOLD = 0.90  # Augmenté de 0.85 à 0.90 pour réduire les fausses détections
        self.STABLE_FRAMES = 5  # Augmenté de 5 à 8 pour exiger plus de stabilité
        self.COOLDOWN_TIME = 5  # Augmenté de 5 à 8 pour plus de temps entre détections
        # Durée réelle (en secondes) que doit couvrir le buffer avant inférence.
        # Calibré pour correspondre à ~30 frames captées à ~30fps (le rythme
        # probable des données d'entraînement). À ajuster si besoin.
        self.TARGET_DURATION = 1.0
        self.MIN_POINTS_FOR_INFERENCE = 10  # nombre minimal de points bruts avant de tenter une inférence

    def init_state(self):
        """Initialise les variables d'état"""
        self.timed_sequence = []    # liste de (timestamp, landmarks) pour le rééchantillonnage
        self.sentence_keywords = []
        self.sentence_lock = threading.Lock()
        self.last_prediction = None
        self.stable_counter = 0
        self.cooldown_counter = 0
        self.no_hands_counter = 0  # Compteur pour le délai de patience
        self.prev_frame_time = time.time()
        self.current_fps = 0.0
        self.sign_detection_start_time = None  # Timestamp du début de détection d'un signe
        self.sign_detection_latencies = []  # Liste des latences de détection pour calculer la moyenne

    def extract_landmarks(self, results):
        """Extrait les landmarks de MediaPipe"""
        face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]) if results.face_landmarks else np.full((468, 3), np.nan)
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]) if results.left_hand_landmarks else np.full((21, 3), np.nan)
        pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark]) if results.pose_landmarks else np.full((33, 3), np.nan)
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]) if results.right_hand_landmarks else np.full((21, 3), np.nan)
        return np.concatenate([face, lh, pose, rh]).astype(np.float32)

    def _process_sentence(self, keywords):
        """Exécuté dans un thread séparé : génération LLM + TTS, ne bloque plus la vidéo."""
        # --- Début de la mesure de latence ---
        start_time = time.time()
        
        print(f"Mots-clés : {keywords}")
        
        # Calculer et afficher la latence moyenne de détection des signes
        with self.sentence_lock:
            if self.sign_detection_latencies:
                avg_detection_latency = sum(self.sign_detection_latencies) / len(self.sign_detection_latencies)
                print(f"⏱️ Latence Détection Signe Moyenne ({len(self.sign_detection_latencies)} signes) : {avg_detection_latency:.3f}s")
                # Réinitialiser pour la prochaine traduction
                self.sign_detection_latencies = []
        
        # Mesure de la traduction LLM
        llm_start = time.time()
        final_sentence = self.sentence_generator.translate(", ".join(keywords))
        llm_time = time.time() - llm_start
        print(f"Phrase : {final_sentence}")
        print(f"⏱️ Latence LLM : {llm_time:.3f}s")
        
        # Mesure de la génération audio
        audio_start = time.time()
        self.text_to_speech.speak(final_sentence)
        audio_time = time.time() - audio_start
        print(f"⏱️ Latence Audio : {audio_time:.3f}s")
        
        # Latence totale (LLM + Audio)
        total_time = time.time() - start_time
        print(f"⏱️ Latence Totale (LLM + Audio) : {total_time:.3f}s")

    def _resample_sequence(self, timed_sequence, num_frames):
        """
        Rééchantillonne une séquence (timestamp, landmarks) vers un nombre fixe
        de points, répartis uniformément sur la durée réelle couverte.
        Ça permet au modèle de voir toujours le même "rythme" de mouvement,
        peu importe le FPS réel du Pi au moment de la capture.
        """
        times = np.array([t for t, _ in timed_sequence], dtype=np.float64)
        data = np.stack([d for _, d in timed_sequence])  # (T, 543, 3)

        t_min, t_max = times[0], times[-1]
        if t_max <= t_min:
            return np.repeat(data[-1:], num_frames, axis=0).astype(np.float32)

        new_times = np.linspace(t_min, t_max, num_frames)
        original_shape = data.shape[1:]  # (543, 3)
        flat = data.reshape(len(times), -1)  # (T, features)
        resampled_flat = np.empty((num_frames, flat.shape[1]), dtype=np.float32)

        for i in range(flat.shape[1]):
            col = flat[:, i]
            valid = ~np.isnan(col)
            if valid.sum() >= 2:
                resampled_flat[:, i] = np.interp(new_times, times[valid], col[valid])
            elif valid.sum() == 1:
                resampled_flat[:, i] = col[valid][0]
            else:
                resampled_flat[:, i] = np.nan

        return resampled_flat.reshape(num_frames, *original_shape)

    def run(self):
        """Boucle principale de traduction"""
        # Configuration optimisée pour Raspberry Pi
        is_pi = "aarch64" in platform.machine() or "armv" in platform.machine()
        if is_pi:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # évite l'accumulation de frames en retard
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            return
        
        # Configuration MediaPipe optimisée pour Pi
        mp_config = {
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5
        }
        if is_pi:
            mp_config["model_complexity"] = 0  # lite : bien plus léger sur Pi
            mp_config["refine_face_landmarks"] = False
            mp_config["smooth_landmarks"] = True
        
        with self.mp_holistic.Holistic(**mp_config) as holistic:
            while self.is_running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret: break

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)
                hands_visible = results.left_hand_landmarks or results.right_hand_landmarks

                # --- Logique de déclenchement de la traduction avec délai de patience ---
                if not hands_visible:
                    if self.sentence_keywords:
                        self.no_hands_counter += 1
                else:
                    self.no_hands_counter = 0

                # Si le compteur dépasse le seuil, on déclenche la traduction
                if self.no_hands_counter > 15:
                    with self.sentence_lock:
                        keywords_snapshot = self.sentence_keywords.copy()
                        self.sentence_keywords = []
                    print(f"Mots-clés : {keywords_snapshot}")
                    # Utiliser le threading pour ne pas bloquer la vidéo
                    threading.Thread(
                        target=self._process_sentence,
                        args=(keywords_snapshot,),
                        daemon=True
                    ).start()
                    self.no_hands_counter = 0

                # --- Logique de classification avec rééchantillonnage temporel ---
                if hands_visible:
                    landmarks = self.extract_landmarks(results)
                    now = time.time()
                    self.timed_sequence.append((now, landmarks))
                    # On garde une marge (1.5x) au-delà de la durée cible pour
                    # avoir toujours assez de points à interpoler.
                    cutoff = now - (self.TARGET_DURATION * 1.5)
                    self.timed_sequence = [p for p in self.timed_sequence if p[0] >= cutoff]
                    status_color = (0, 255, 0)
                else:
                    if self.timed_sequence:
                        self.timed_sequence.pop(0)
                    status_color = (0, 0, 255)

                display_text = ""

                # Durée réellement couverte par le buffer actuel
                span = (self.timed_sequence[-1][0] - self.timed_sequence[0][0]) if len(self.timed_sequence) >= 2 else 0.0
                has_enough_data = (
                    len(self.timed_sequence) >= self.MIN_POINTS_FOR_INFERENCE
                    and span >= self.TARGET_DURATION * 0.5  # au moins la moitié de la durée cible couverte
                )

                if has_enough_data and hands_visible and self.cooldown_counter == 0:
                    input_data = self._resample_sequence(self.timed_sequence, self.MAX_FRAMES)
                    output = self.prediction_fn(inputs=input_data)
                    prediction_probs = output['outputs']
                    idx = np.argmax(prediction_probs)
                    confidence = prediction_probs[idx]
                    current_sign = self.actions.get(idx, "???")

                    if confidence > self.THRESHOLD:
                        if current_sign == self.last_prediction:
                            self.stable_counter += 1
                        else:
                            self.stable_counter = 0
                            self.last_prediction = current_sign
                            # Enregistrer le début de détection d'un nouveau signe
                            self.sign_detection_start_time = time.time()

                        if self.stable_counter >= self.STABLE_FRAMES:
                            with self.sentence_lock:
                                if not self.sentence_keywords or self.sentence_keywords[-1] != current_sign:
                                    # Calculer et stocker la latence de détection du signe
                                    if self.sign_detection_start_time:
                                        detection_latency = time.time() - self.sign_detection_start_time
                                        self.sign_detection_latencies.append(detection_latency)
                                    
                                    self.sentence_keywords.append(current_sign)
                                    self.cooldown_counter = self.COOLDOWN_TIME
                            self.stable_counter = 0

                        display_text = f"En cours : {current_sign} ({confidence:.2f})"
                    else:
                        self.stable_counter = 0
                        display_text = "Signe incertain..."

                elif self.cooldown_counter > 0:
                    self.cooldown_counter -= 1
                    display_text = "Validation en cours..."

                # Calcul du FPS
                curr_time = time.time()
                elapsed = curr_time - self.prev_frame_time
                self.prev_frame_time = curr_time
                if elapsed > 0:
                    self.current_fps = 1.0 / elapsed

                # --- Stockage du frame pour le streaming web ---
                cv2.rectangle(frame, (0, 430), (640, 480), (0, 0, 0), -1)
                cv2.putText(frame, "Phrase: " + " ".join(self.sentence_keywords[-5:]), 
                            (10, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.circle(frame, (30, 30), 10, status_color, -1)
                cv2.putText(frame, display_text, (50, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (245, 117, 16), 2)
                cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (540, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Stocker le frame courant pour le streaming
                self.current_frame = frame
                self.current_text = display_text
                self.current_status = "Actif" if hands_visible else "En attente"
                self.current_sentence = " ".join(self.sentence_keywords[-5:])

        if self.cap:
            self.cap.release()

    def start(self):
        """Démarre le moteur de traduction dans un thread séparé"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            return True
        return False

    def stop(self):
        """Arrête le moteur de traduction"""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join(timeout=5)
            return True
        return False


# Instance globale du moteur de traduction
translation_engine = TranslationEngine()
