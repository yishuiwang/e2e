import os
from pathlib import Path
from huggingface_hub import snapshot_download


MODEL_ID = "hfl/chinese-roberta-wwm-ext"


def main():
    this_dir = Path(__file__).parent
    target_dir = this_dir / "models" / "hfl-chinese-roberta-wwm-ext"
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {MODEL_ID} to {target_dir} ...")
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print("Done.")


if __name__ == "__main__":
    main()
