import argparse 
import os

from mget import Globals, download

if __name__ == "__main__":
    gbl = Globals()
    parser = argparse.ArgumentParser()
    parser.add_argument("url")

    parser.add_argument(
		"-t",
		"--threads",
		type=int,
		default=os.cpu_count(),
		help="Number of threads to spawn to help download."
	)

    parser.add_argument(
		"-p",
		"--path",
		default=os.getcwd(),
		help="Path to download to (If you want to set an output file name, use --output)"
	)

    parser.add_argument(
		"-o",
		"--output",
		help="Output filename"
	)

    parser.add_argument(
		"-c",
		"--chunk",
		default=2048,
		type=int,
		help="Chunk size to read in bytes. If set too high, it can cause some read lag and slow down the download"
	)

    args = parser.parse_args()

    download(
		args.url,
		gbl,
		args.path,
		args.output,
		args.threads,
		args.chunk
	)
