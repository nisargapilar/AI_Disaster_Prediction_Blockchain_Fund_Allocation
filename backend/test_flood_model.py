import zipfile
import json
import tempfile
import shutil
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.models import load_model


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml_training"
    / "flood"
    / "models"
    / "flood_corrected_lstm.keras"
)


print("TensorFlow:", tf.__version__)
print("Model:", MODEL_PATH)


with tempfile.TemporaryDirectory() as temp_dir:

    temp_model = Path(temp_dir) / "flood_fixed.keras"

    with zipfile.ZipFile(MODEL_PATH, "r") as zin:

        with zipfile.ZipFile(
            temp_model,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zout:

            for item in zin.infolist():

                data = zin.read(item.filename)

                if item.filename == "config.json":

                    config = json.loads(
                        data.decode("utf-8")
                    )

                    def clean(obj):

                        if isinstance(obj, dict):

                            if (
                                obj.get("class_name")
                                == "GlorotUniform"
                            ):

                                obj.get(
                                    "config",
                                    {}
                                ).pop(
                                    "input_axes",
                                    None
                                )

                                obj.get(
                                    "config",
                                    {}
                                ).pop(
                                    "output_axes",
                                    None
                                )

                            for value in obj.values():
                                clean(value)

                        elif isinstance(obj, list):

                            for value in obj:
                                clean(value)

                    clean(config)

                    data = json.dumps(
                        config
                    ).encode("utf-8")

                zout.writestr(
                    item,
                    data
                )

    print("Temporary fixed model created.")

    model = load_model(
        temp_model,
        compile=False
    )

    print()
    print("==============================")
    print("FLOOD MODEL LOAD OK")
    print("==============================")
    print("Input shape:", model.input_shape)
    print("Output shape:", model.output_shape)