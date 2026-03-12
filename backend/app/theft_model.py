from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import cv2
import numpy as np

try:
    import tensorflow as tf
    from tensorflow.keras import Input, Model
    from tensorflow.keras.layers import Add, Conv3D, Dense, Flatten, Lambda, MaxPooling3D
except Exception as exc:  # pragma: no cover
    tf = None
    Input = Model = Add = Conv3D = Dense = Flatten = Lambda = MaxPooling3D = None
    TF_IMPORT_ERROR = exc
else:  # pragma: no cover
    TF_IMPORT_ERROR = None


class TheftModelRuntimeError(RuntimeError):
    pass


class TheftDetectionModel:
    def __init__(
        self,
        weights_path: str | Path,
        threshold: float = 0.6,
        resize: Tuple[int, int] = (224, 224),
        clip_frames: int = 64,
    ) -> None:
        self.weights_path = Path(weights_path).expanduser()
        self.threshold = threshold
        self.resize = resize
        self.clip_frames = clip_frames
        self.model = None

    def _get_rgb(self, input_x):
        return input_x[..., :3]

    def _data_layer(self, input_x, stride):
        return tf.gather(input_x, tf.range(0, self.clip_frames, stride), axis=1)

    def _sample(self, input_x, stride):
        return tf.gather(input_x, tf.range(0, input_x.shape[1], stride), axis=1)

    def _merging_block(self, x):
        x = Conv3D(64, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = Conv3D(64, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = MaxPooling3D(pool_size=(2, 2, 2))(x)
        x = Conv3D(64, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = Conv3D(64, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = MaxPooling3D(pool_size=(2, 2, 2))(x)
        x = Conv3D(128, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = Conv3D(128, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        return x

    def _get_fast_path(self, fast_input):
        connection_dic = {}
        rgb = Lambda(self._get_rgb, output_shape=None)(fast_input)

        rgb = Conv3D(16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)
        rgb = Conv3D(16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)
        connection_dic["con-1"] = Lambda(self._sample, arguments={"stride": 18}, name="con_1")(rgb)

        rgb = Conv3D(32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)
        rgb = Conv3D(32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)
        connection_dic["con-2"] = Lambda(self._sample, arguments={"stride": 18}, name="con_2")(rgb)
        return rgb, connection_dic

    def _get_slow_path(self, slow_input, connection_dic):
        rgb = Lambda(self._get_rgb, output_shape=None)(slow_input)
        con_1 = connection_dic["con-1"]
        con_2 = connection_dic["con-2"]

        rgb = Conv3D(16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)
        rgb = Conv3D(16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)

        rgb = Add(name="connection_1_rgb")([rgb, con_1])
        rgb = Conv3D(32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)
        rgb = Conv3D(32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = Conv3D(32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(rgb)
        rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)

        x = Add(name="connection_2_rgb")([rgb, con_2])
        x = MaxPooling3D(pool_size=(1, 2, 2))(x)
        x = Conv3D(64, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = Conv3D(64, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = MaxPooling3D(pool_size=(2, 2, 2))(x)
        x = Conv3D(64, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = Conv3D(64, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = MaxPooling3D(pool_size=(2, 2, 2))(x)
        x = Conv3D(128, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        x = Conv3D(128, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer="he_normal", activation="relu", padding="same")(x)
        return x

    def _build_model(self):
        clip_input = Input(shape=(self.clip_frames, self.resize[1], self.resize[0], 3))
        slow_input = Lambda(self._data_layer, arguments={"stride": 16}, name="slow_input")(clip_input)
        fast_rgb, connections = self._get_fast_path(clip_input)
        slow_rgb = self._get_slow_path(slow_input, connections)
        merged = Add(name="ADD_slow_rgb_ans_fast_rgb_opt")([self._merging_block(fast_rgb), slow_rgb])
        merged = Flatten()(merged)
        merged = Dense(128, activation="relu")(merged)
        merged = Dense(32, activation="relu")(merged)
        predictions = Dense(3, activation="softmax")(merged)
        return Model(inputs=clip_input, outputs=predictions)

    def ensure_loaded(self) -> None:
        if self.model is not None:
            return
        if tf is None:
            raise TheftModelRuntimeError(f"TensorFlow is not available: {TF_IMPORT_ERROR}")
        if not self.weights_path.exists():
            raise TheftModelRuntimeError(f"Model weights not found: {self.weights_path}")
        self.model = self._build_model()
        self.model.load_weights(str(self.weights_path))

    def _uniform_sampling(self, video_frames: np.ndarray) -> np.ndarray:
        frame_count = int(len(video_frames))
        interval = int(np.ceil(frame_count / self.clip_frames))
        sampled = [video_frames[i] for i in range(0, frame_count, interval)]
        missing = self.clip_frames - len(sampled)
        if missing > 0:
            for index in range(-missing, 0):
                sampled.append(video_frames[index] if frame_count + index >= 0 else video_frames[0])
        return np.asarray(sampled, dtype=np.float32)

    @staticmethod
    def _normalize(video_frames: np.ndarray) -> np.ndarray:
        mean = float(np.mean(video_frames))
        std = float(np.std(video_frames))
        if std < 1e-6:
            return video_frames - mean
        return (video_frames - mean) / std

    def preprocess_frames(self, frames: Sequence[np.ndarray]) -> np.ndarray:
        if not frames:
            raise TheftModelRuntimeError("No frames available for inference")

        formatted_frames: List[np.ndarray] = []
        width, height = self.resize
        for frame in frames:
            resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            formatted_frames.append(rgb.astype(np.float32))

        sampled = self._uniform_sampling(np.asarray(formatted_frames, dtype=np.float32))
        sampled[..., :3] = self._normalize(sampled[..., :3])
        return sampled.reshape((-1, self.clip_frames, height, width, 3))

    def predict_frames(self, frames: Sequence[np.ndarray]) -> Dict[str, float | str | bool]:
        self.ensure_loaded()
        predictions = self.model.predict(self.preprocess_frames(frames), verbose=0)[0]
        bag, clothes, normal = [float(value) for value in predictions]
        suspicious_confidence = max(bag, clothes)
        detected = suspicious_confidence > normal and suspicious_confidence >= self.threshold

        if bag >= clothes:
            activity_type = "Theft - Bag Concealment"
            event_index = 0
        else:
            activity_type = "Theft - Clothing Concealment"
            event_index = 1

        if not detected:
            activity_type = "Normal Activity"
            event_index = 2

        severity = "high" if suspicious_confidence >= 0.8 else "medium"
        return {
            "detected": detected,
            "confidence": round(suspicious_confidence, 3),
            "activity_type": activity_type,
            "severity": severity,
            "bag": round(bag, 3),
            "clothes": round(clothes, 3),
            "normal": round(normal, 3),
            "event_index": event_index,
            "source": "ml-model",
        }
