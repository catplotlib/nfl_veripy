### About
This repository provides Analyzer, Propagator, and Partitioner classes from the LCSS/ACC '21 paper.
We import `auto_LIRPA`, `crown_ibp` and `robust_sdp` codebases from open source repositories (as Git submodules) and implement `Partitioner` methods from Xiang '17 and Xiang '20 in Python (open source implementation is in Matlab), along with our own methods from the paper.

### Get the code

```bash
git clone --recursive git@gitlab.com:mit-acl/ford_ugvs/robustness_analysis.git
```

### Install

In the root of this directory:
```bash
python -m pip install -e .
python -m pip install -e crown_ibp
python -m pip install -e partition
python -m pip install -e robust_sdp
python -m pip install -e auto_LIRPA
```

Now you can import things like:
```bash
>>> from reach_lp.reach_lp import reachLP_1
>>> import crown_ibp.bound_layers
```

## Reproduce Figures from LCSS/ACC 2021 Paper

### Figure 4

Figure 4a (Lower Bounds):
```bash
python -m partition.Analyzer \
	--partitioner GreedySimGuided \
	--propagator CROWN_LIRPA \
	--term_type time_budget \
	--term_val 2 \
	--interior_condition lower_bnds \
	--model random_weights \
	--activation relu \
	--show_input True
```
![Fig. 4a](docs/_static/random_weights_relu_GreedySimGuided_CROWN_LIRPA_interior_condition_lower_bnds_num_simulations_10000.0_termination_condition_type_time_budget_termination_condition_value_2.0.png)

Figure 4b (Linf Ball):
```bash
python -m partition.Analyzer \
	--partitioner GreedySimGuided \
	--propagator CROWN_LIRPA \
	--term_type time_budget \
	--term_val 2 \
	--interior_condition linf \
	--model random_weights \
	--activation relu \
	--show_input True
```
![Fig. 4b](docs/_static/analyzer/random_weights_relu_GreedySimGuided_CROWN_LIRPA_interior_condition_linf_num_simulations_10000.0_termination_condition_type_time_budget_termination_condition_value_2.0.png)

Figure 4c (Convex Hull):
```bash
python -m partition.Analyzer \
	--partitioner GreedySimGuided \
	--propagator CROWN_LIRPA \
	--term_type time_budget \
	--term_val 2 \
	--interior_condition convex_hull \
	--model random_weights \
	--activation relu \
	--show_input True
```
![Fig. 4c](docs/_static/analyzer/random_weights_relu_GreedySimGuided_CROWN_LIRPA_interior_condition_convex_hull_num_simulations_10000.0_termination_condition_type_time_budget_termination_condition_value_2.0.png)

### Figure 6

```bash
python -m partition.Analyzer \
	--partitioner SimGuided \
	--propagator IBP_LIRPA \
	--term_type time_budget \
	--term_val 2 \
	--interior_condition conv_hull \
	--model robot_arm \
	--activation tanh
```

```bash
python -m partition.Analyzer \
	--partitioner AdaptiveSimGuided \
	--propagator CROWN_LIRPA \
	--term_type time_budget \
	--term_val 2 \
	--interior_condition conv_hull \
	--model robot_arm \
	--activation tanh
```


---

### Figure 4
To reproduce this figure, please run:
```bash
python -m partition.Analyzer
```
This should pop up with a matplotlib window showing the partition being refined.
You can change the `type` in `partitioner_hyperparams` at the bottom of `Analyzer.py` to modify which Partitioner is used.

### Figure 5
To reproduce this figure, please run:
```bash
python -m partition.Analyzer
```
This should pop up with a matplotlib window showing the partition being refined.
You can change the `interior_condition` in `partitioner_hyperparams` at the bottom of `Analyzer.py` to modify which output shape is produced.

### Figure 6
To reproduce this figure, please run:
```bash
python -m partition.experiments
```
This will iterate through combinations of `Partitioner`, `Propagator` and termination conditions and produce a timestamped `.pkl` file in `results` containing a `pandas` dataframe with the results.

To plot the data from this dataframe (it should happen automatically by running `experiments.py`), comment out `df = experiment()` in `experiments.py` and it will just load the latest dataframe and plot it.
You can switch which x axis to use with the argument of `plot()`.

### Figure 7a
This one unfortunately requires code for the RL implementation that is under IP protection.

### Figure 7b
Collect training data, train a Keras model, and evaluate the reachable set using
```bash
python -m partition.dynamics
```




---

## Older stuff

### Examples

See the implementation of Xiang 2017 and Xiang 2020:
```bash
python -m partition.xiang
```

This will pop up with:
- their randomly initialized DNN & 25 uniform partitioned inputs (from Xiang 2017)
- their robot arm example using CROWN & IBP and Uniform & Simulation-Guided partitioning (from Xiang 2020)


### tmp
```bash
source ~/code/gym-collision-avoidance/venv/bin/activate
```

### getting julia code to work

- Install julia via https://julialang.org/downloads
- Be sure to create a pointer to the executable (https://julialang.org/downloads/platform/)
```bash
# For OSX:
ln -s /Applications/Julia-<version>.app/Contents/Resources/julia/bin/julia /usr/local/bin/julia
```
- Install NeuralVerification.jl from Stanford's github
```bash
julia
# Press `]`
add https://github.com/sisl/NeuralVerification.jl
```
- Install pyjulia
```bash
python -m pip install julia
```
