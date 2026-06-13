# jet3D Take-Home Challenge

### ⏱️ ***We expect this to be a 3-4 hour exercise.***
You won’t be able to solve everything in that amount of time, and that’s okay — prioritize what you believe matters most. We want to see your judgment, clarity, and design thinking in action.

## 1. Overview and Expectations

Welcome! This take-home challenge introduces a simplified but realistic scenario drawn from our work at Boom Supersonic. As software engineers embedded across hardware and engineering teams, we often help build internal tools that automate workflows, improve simulation throughput, and make engineering data more usable.

This challenge simulates one such situation. The code you'll work with was written by a domain expert — a skilled aerospace engineer solving real problems, but not focused on software engineering discipline. Your task is to:

- Understand their current workflow and tools.
- **Refactor and clean up the code to improve readability, maintainability, and extensibility.**
- Think through how to scale and systematize the process.

This is an open-ended challenge. We’re evaluating your ability to:

- Interpret and improve poor/fragile code.
- Reason about scaling and system integration.
- Communicate tradeoffs and design decisions.

Your final submission should include:

- Cleaned-up, modular, and testable code.
- A written discussion in [NOTES.md](./NOTES.md) covering both the changes you made and your broader architectural thinking.

> ⚠️ We expect real code improvements.
You should spend time reading and cleaning up the current code. Apply good software engineering practices to make it easier to use, extend, and maintain.

## 2. Scenario: Simulation at Scale

Computational Fluid Dynamics (CFD) solvers are highly complex, specialized programs that use sophisticated mathematical techniques to simulate fluid behavior—such as airflow around an aircraft. Because these solvers are typically provided as external software that we can't directly modify, any performance or usability enhancements must come from the systems we build around them.

An aerospace engineer on your team is using the jet3D CFD solver to simulate aerodynamic forces and moments for design analysis. For a CFD solver, jet3D is fast (about 5 seconds per case), but error-prone.

The engineer originally wrote a script to generate inputs, call jet3D, and post-process the results. This works fine for one-off cases or small batches when run on the engineer's own system. However, they now need to run a sweep of over 300,000 cases, presenting a number of issues.

### The Issues

- Serial execution on the engineer's system will take more than 2 weeks of compute time, if all cases run without error.
- jet3D has a **20–30% failure rate**, including:
  - Random solver errors (e.g. segfaults, timeouts, IO errors)
  - Output file truncation
  - System hangs
- Postprocessing is manual and fragile, requiring inspection of each output file.
- Postprocessing is not set up to allow an engineer to explore a large set of results efficiently.
- Rerunning failed cases is manual and error-prone.

They’ve asked for your help to make the workflow faster, more robust, and easier to analyze at scale.

## 3. How to Run the Current Tool

The engineer currently uses a command-line Python script to interact with the jet3D solver. The script supports a few basic modes described below:

**NOTE:** *to run these commands open the terminal by either clicking “All Tools”, then select “Shell” on the left sidebar or with:*

`ctrl + backtick`

Copy and paste this command in terminal to run a single simulation:

`./src/runner.py --single --pressure 101325 --temperature 288.15 --mach 0.85`

Copy and paste this command in terminal to run a sweep from a file (input.dat):

`./src/runner.py --sweep ./input.dat`

Copy and paste this command in terminal to post-process a single result:

`./src/runner.py --postprocess result_case_m0.85_p101325_t288.15.log`

## 4. The Challenge

We want to see what you would do to improve this system. It’s intentionally messy. Your challenge is to:

- Make the code cleaner, easier to test, and more maintainable.
- Design a more scalable and fault-tolerant execution workflow.
- Improve visibility into which cases succeeded or failed.
- Propose a better postprocessing and analysis pipeline.
- Think about integration with other systems: batch execution, job tracking, or even cloud queues. (It's not a requirement to integrate this with an actual cloud, but if there is time one could show sample snippets of how this would work, or configuration files, etc)

> ⚠️ **DO NOT modify the jet3D file.**
The jet3D solver provided with this challenge is a simulated binary. Treat it as a black box — the goal is to build tools that work around its behavior, not to change it directly.

## 5. Document Up Your Approach

Please use the included [NOTES.md](./NOTES.md) file to:

- Explain why and how you cleaned up the code.
- Describe any improvements to the structure, naming, or testability.
- Discuss what you’d build or integrate if given more time.
- Propose any systems you’d use for queuing, batch compute, data management, etc.

This is a two-part interview:

1. **Code** – Can you clean up, understand, and improve messy, real-world code?
1. **Design** – Can you justify your thinking and propose scalable improvements?

At Boom, time-to-insight matters. Waiting days or weeks for simulation results is unacceptable — this is where software engineering discipline and tooling can make a big difference.

We’re excited to see how you’d approach it!

## Reminders, Hints, & Tips

- This is intended to take about ***3 hours*** — please don’t burn yourself out spending all day on it.
- If an error occurs when you run one of the commands try re-running it - remember, the jet3D solver is flaky!

### Specific Actions in the project

We made a [pyproject.toml](./pyproject.toml) for you that is somewhat generic and should get you started.

If you're familiar with the syntax, feel free to customize it to your favorite tools or patterns. But if you're not, what follows is some common actions.

#### Add dependencies

Editing the `dependencies = ` array in [pyproject.toml](./pyproject.toml) should give you access to installing things.

After saving, follow up with
```shell
pip install -e .
```

to reinstall your package.


#### Make your own python package

If you want to make your own python package as part of organizing the code, do something like

```shell
mkdir src/my_package
touch src/my_package/__init__.py
pip install -e .
```
