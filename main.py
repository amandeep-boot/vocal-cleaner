import argparse
from cleaner import pipeline

def main():
    parser = argparse.ArgumentParser(description="Vocal Cleaner MVP")
    parser.add_argument("--input",  required=True, help="Path to raw vocal file")
    parser.add_argument("--output", required=True, help="Output folder path")
    args = parser.parse_args()

    pipeline.run(
        input_path=args.input,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()