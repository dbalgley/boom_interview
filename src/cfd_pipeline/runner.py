#!/usr/bin/env python3

import argparse
import os
import subprocess


def runner():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir", default="./cases", help="Directory to use for inputs and outputs"
    )
    parser.add_argument(
        "--sweep", type=str, help="Path to input.dat file for sweep of input cases"
    )
    parser.add_argument(
        "--single", action="store_true", help="Generate and run a single input file"
    )
    parser.add_argument("--pressure", type=int, help="Pressure value for single input")
    parser.add_argument(
        "--temperature", type=float, help="Temperature value for single input"
    )
    parser.add_argument("--mach", type=float, help="Mach value for single input")
    parser.add_argument(
        "--postprocess", help="Postprocess a single result file by name"
    )
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    if args.single:
        if args.pressure is None or args.temperature is None or args.mach is None:
            print(
                "[runner] ERROR: --pressure, --temperature, and --mach must be specified for single run"
            )
            return
        pressure = args.pressure
        temperature = args.temperature
        mach = args.mach

        case_name = f"m{mach}_p{pressure}_t{temperature}"
        input_path = os.path.join(args.dir, f"input_case_{case_name}.txt")
        output_path = os.path.join(args.dir, f"result_case_{case_name}.log")

        with open(input_path, "w") as f:
            f.write(f"pressure={pressure}\n")
            f.write(f"temperature={temperature}\n")
            f.write(f"mach={mach}\n")

        try:
            print(f"[runner] Running case {case_name}...")
            result = subprocess.run(
                ["./bin/jet3D", input_path, output_path], capture_output=True, text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                print(
                    f"[runner] ERROR running case {case_name}: {result.stderr.strip()}"
                )
            else:
                print(f"[runner] SUCCESS input: {input_path}, output:{output_path}")
        except Exception as e:
            print(f"[runner] FAILED to run case {case_name}: {e}")

    elif args.sweep:
        try:
            with open(args.sweep, "r") as sweep_file:
                lines = sweep_file.readlines()[1:]  # Skip header line
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) != 3:
                        print(f"[runner] Skipping malformed line: {line.strip()}")
                        continue
                    pressure = int(parts[0])
                    temperature = float(parts[1])
                    mach = float(parts[2])

                    case_name = f"m{mach}_p{pressure}_t{int(temperature)}"
                    input_path = os.path.join(args.dir, f"input_case_{case_name}.txt")
                    output_path = os.path.join(args.dir, f"result_case_{case_name}.log")

                    with open(input_path, "w") as f:
                        f.write(f"pressure={pressure}\n")
                        f.write(f"temperature={temperature}\n")
                        f.write(f"mach={mach}\n")

                    try:
                        print(f"[runner] Running case {case_name}...")
                        result = subprocess.run(
                            ["./bin/jet3D", input_path, output_path],
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )
                        print(result.stdout)
                        if result.returncode != 0:
                            print(
                                f"[runner] ERROR running case {case_name}: {result.stderr.strip()}"
                            )
                        else:
                            print(
                                f"[runner] SUCCESS input: {input_path}, output:{output_path}"
                            )
                    except subprocess.TimeoutExpired:
                        print(f"[runner] TIMEOUT on case {case_name}")
                    except Exception as e:
                        print(f"[runner] FAILED to run case {case_name}: {e}")
        except FileNotFoundError:
            print(f"[runner] ERROR: Sweep file not found: {args.sweep}")

    elif args.postprocess:
        output_file = os.path.join(args.dir, args.postprocess)
        if not os.path.exists(output_file):
            print(f"[postprocess] File not found: {output_file}")
            return
        try:
            with open(output_file) as f:
                lines = f.readlines()
                found = False
                for line in lines:
                    if "Final Forces and Moments" in line:
                        parts = line.strip().split(":")
                        if len(parts) > 1:
                            values = parts[1].strip(" []").split(",")
                            if len(values) == 6:
                                fx, fy, fz, mx, my, mz = map(float, values)
                                print(f"[postprocess] Fx (N): {fx}")
                                print(f"[postprocess] Fy (N): {fy}")
                                print(f"[postprocess] Fz (N): {fz}")
                                print(f"[postprocess] Mx (Nm): {mx}")
                                print(f"[postprocess] My (Nm): {my}")
                                print(f"[postprocess] Mz (Nm): {mz}")
                                found = True
                                break
                if not found:
                    print(
                        f"[postprocess] No results found in {output_file} — file may be truncated or invalid."
                    )
        except Exception as e:
            print(f"[postprocess] Failed to read {output_file}: {e}")
    else:
        print(
            "[runner] No action specified. Use --single, --sweep INPUT.DAT, or --postprocess FILE"
        )


if __name__ == "__main__":
    runner()
