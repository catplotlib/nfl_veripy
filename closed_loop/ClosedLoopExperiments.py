from importlib import reload
import partition
import partition.Partitioner
#import partition.Analyzer
import partition.Propagator
#from partition.models import model_xiang_2020_robot_arm, model_gh1, model_gh2, random_model, lstm
import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt
from matplotlib import cm
from datetime import datetime
import os
import glob
import time
import math
from closed_loop.nn import load_model
from closed_loop.Dynamics import DoubleIntegrator, Quadrotor
import closed_loop.ClosedLoopAnalyzer

from closed_loop.ClosedLoopPartitioner import ClosedLoopNoPartitioner, ClosedLoopUniformPartitioner
from closed_loop.ClosedLoopPropagator import ClosedLoopCROWNPropagator, ClosedLoopIBPPropagator, ClosedLoopFastLinPropagator, ClosedLoopSDPPropagator
from closed_loop.ClosedLoopConstraints import PolytopeInputConstraint, LpInputConstraint, PolytopeOutputConstraint, LpOutputConstraint

save_dir = "{}/results/experiments/closed_loop/".format(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(save_dir, exist_ok=True)
img_save_dir = save_dir+"/imgs/"
os.makedirs(img_save_dir, exist_ok=True)

model_list= [
  #  {
    #    'neurons': (2,100,2),
    #    'activation': 'relu',
     #   'seeds': range(10),
    #    'name': "Small NN",
  #  },
   # {
      #  'neurons': (2,10,20,50,20,10,2),
     #   'neurons': (2, 100, 100, 100, 100, 100, 100, 2),

    #    'activation': 'relu',
    #    'seeds': range(10),
    #    'name': "Deep NN",
   # },
    # {
    #     'model_fn': cnn_2layer,
    #     'model_args': {
    #         'in_ch': 1,
    #         'in_dim': 4,
    #         'width': 4,
    #         'linear_size': 16,
    #         'out_dim': 2,
    #     },
    #     'seeds': range(10),
    #     'name': "CNN",
    # },
    # {
    #     'model_fn': lstm,
    #     'model_args': {
    #         'hidden_size': 64, 
    #         'num_classes': 2, 
    #         'input_size': 64,
    #         'num_slices': 8,
    #     },
    #     'input_shape': (8,8),
    #     'lstm': True,
    #     'seeds': range(10),
    #     'name': "LSTM",
    # },
   



    {
        'model_fn': 'double_integrator_mpc',
        'input_range': np.array([ # (num_inputs, 2)
                      [2.5, 3.0], # x0min, x0max
                      [-0.25, 0.25], # x1min, x1max
                      ]),
        'seeds': range(1),
        'name': "double Integrator",
        },
   {
        'model_fn': 'quadrotor',
 
       'seeds': range(1),
       'name': "quadrotor",

       'input_range':np.array([ # (num_inputs, 2)
                     [4.65,4.65,2.95,0.94,-0.01,-0.01],
                      [4.75,4.75,3.05,0.96,0.01,0.01]
        ]).T
        },
     #{
     #    'model_fn': random_model,
    #     'model_args': {
     #        'neurons': (2,100,100,100,100,100,100,2),
      #       'activation': 'relu',
    #     },
    #     'seeds': range(10),
    #     'name': "Deep NN",
    # },
    # {
    #     'model_fn': random_model,
    #     'model_args': {
    #         'neurons': (4,100,100,10),
    #         'activation': 'relu',
    #     },
    #     'seeds': range(10),
    #     'name': "Larger Input/Output Dims",
    # },
  #  {
     #   'neurons': (2,5,10),
   #     'activation': 'relu',
   #     'seeds': range(10),
   #     'name': "Larger Output Dimension",
  #  },
   
]

def collect_data_for_table(propagators,partitioners, experiments_list, experiment_hyperparams, model_params, boundaries):

    df = pd.DataFrame()

    #for model_param in model_params:  ## TODO: fix it for creating the table
    for seed in model_params['seeds']:
        model_fn = model_params['model_fn']
        #model, model_info = model_fn(seed=seed, **experiment['model_args'])
        model = load_model(model_fn)
    
    ##############
    # System Dynamics
    ##############
        if model_fn == 'double_integrator_mpc':

            dynamics = DoubleIntegrator()
            init_state_range = model_params['input_range']
                
        elif model_fn == 'quadrotor':

            dynamics = Quadrotor()
            init_state_range = model_params['input_range']
        else:
                
            raise NotImplementedError

          #  input_range = experiment_input_range(lstm=('lstm' in experiment and experiment['lstm']),
           #     neurons=experiment['model_args']['neurons'], input_shape=experiment.get('input_shape', None))
        df = run_experiment(model=model, dynamics =dynamics,  model_info=None, df=df, save_df=False, input_range=init_state_range, 
                partitioners=partitioners, propagators=propagators, partitioner_hyperparams_to_use=partitioner_hyperparams_to_use,
                experiments= experiments_list, experiment_hyperparams= experiment_hyperparams)

    # Save the df in the "results" dir (so you don't have to re-run the expt)
    current_datetime = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    df.to_pickle("{}/{}.pkl".format(save_dir, current_datetime))
    return df

def run_experiment(model=None, dynamics= None, model_info=None, df=None, save_df=True, input_range=None,
 partitioners=None, propagators=None, partitioner_hyperparams_to_use=None, experiments =None, experiment_hyperparams=None):
  
    if model is None or dynamics is None:
     #   neurons = [10,5,2]
       # model, model_info = random_model(activation='relu', neurons=neurons, seed=0)
        raise NotImplementedError

    if input_range is None:
        raise NotImplementedError

        # # For CNN
        # input_range = np.zeros((1, 4, 4)+(2,))
        # input_range[0,0,0,1] = 1.

        # # For LSTM
        # input_shape = (8,8)
        # input_range = np.zeros(input_shape+(2,))
        # input_range[-1,0:2,1] = 1.

        # For random models
      #  input_range = np.zeros((model_info['model_neurons'][0],2))
      #  input_range[:,1] = 1.
      #  input_range[0,1] = 1.
      #   input_range[1,1] = 1.


    if partitioners is None or propagators is None or partitioner_hyperparams_to_use is None or experiments is None or experiment_hyperparams is None:
        # Select which algorithms and hyperparameters to evaluate
        # partitioners = ["SimGuided", "GreedySimGuided", "UnGuided"]
        # partitioners = ["AdaptiveSimGuided", "SimGuided", "GreedySimGuided"]
        partitioners = ["None", "Uniform"] #SimGuided", "GreedySimGuided"]
        # partitioners = ["UnGuided"]
        # propagators = ["SDP"]
        propagators = ["IBP", "CROWN", "FastLin" ]#, "SDP"]
        experiments = ["errorVsPartitions"]
        partitioner_hyperparams_to_use = {
        "None":
                {
                },
            
        "Uniform":
                {
                    "num_partitions": np.array([4,4]),
        }
        }
        
        experiment_hyperparams={
        "errorVsPartitions":
                {
                    "t_max" : 5,
                }
        }

    # Auto-run combinations of algorithms & hyperparams, log results to pandas dataframe
    if df is None:
        df = pd.DataFrame()

    analyzer = closed_loop.ClosedLoopAnalyzer.ClosedLoopAnalyzer(model, dynamics)
    #analyzer = partition.Analyzer.Analyzer(model)
    for partitioner, propagator,experiment in itertools.product(partitioners, propagators, experiments):
        partitioner_keys = list(partitioner_hyperparams_to_use[partitioner].keys())
        partitioner_hyperparams = {"type": partitioner}
        exp_keys = list(experiment_hyperparams[experiment].keys())
        for partitioner_vals in itertools.product(*list(partitioner_hyperparams_to_use[partitioner].values())):


            for partitioner_i in range(len(partitioner_keys)):
                partitioner_hyperparams[partitioner_keys[partitioner_i]] = partitioner_vals[partitioner_i]
            propagator_hyperparams = {"type": propagator, "input_shape": input_range.shape[:-1]}
            #if model_info["model_neurons"][-1] == 2 or partitioner_hyperparams["interior_condition"] is not "convex_hull":
            for exp_vals in itertools.product(*list(experiment_hyperparams[experiment].values())):
                if  (len(exp_keys)==1  and  't_max' in exp_keys[0]):
                    t_max = exp_vals[0]
    
                else:
                    raise NotImplementedError
                data_row = run_and_add_row(analyzer, input_range, partitioner_hyperparams, propagator_hyperparams, model_info, t_max)
                df = df.append(data_row, ignore_index=True)
    
    # Also record the "exact" bounds (via sampling) in the same dataframe
   # output_range_exact = analyzer.get_exact_output_range(input_range)


    if save_df:
        # Save the df in the "results" dir (so you don't have to re-run the expt)
        current_datetime = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        df.to_pickle("{}/{}.pkl".format(save_dir, current_datetime))

    return df

def run_and_add_row(analyzer, input_range, partitioner_hyperparams, propagator_hyperparams, model_info={}, t_max=5):
    print("Partitioner: {},\n Propagator: {},\n Time steps:{}".format(partitioner_hyperparams, propagator_hyperparams, t_max))
    np.random.seed(0)
    analyzer.partitioner = partitioner_hyperparams
    analyzer.propagator = propagator_hyperparams
   # t_start = time.time()
   # output_range, analyzer_info = analyzer.get_output_range(init_state_range)
   # t_end = time.time()
    
    #np.random.seed(0)
   # if partitioner_hyperparams["interior_condition"] == "convex_hull":
   #     exact_hull = analyzer.get_exact_hull(input_range, N=int(1e5))
  #      error = analyzer.partitioner.get_error(exact_hull, analyzer_info["estimated_hull"])
  #  else:
    
    input_constraint = LpInputConstraint(range=input_range, p=np.inf)
    output_constraint = LpOutputConstraint(p=np.inf)
    #output_constraint, analyzer_info = analyzer.get_reachable_set(input_constraint, output_constraint, t_max)
    output_constraint, analyzer_info = analyzer.get_reachable_set(input_constraint, output_constraint, t_max)
   # print("output_constraint:", output_constraint)
    # output_range, analyzer_info = analyzer.get_output_range(input_range)
    # print("Estimated output_range:\n", output_range)
    # print("Number of propagator calls:", analyzer_info["num_propagator_calls"])
    # 
    # print(t_end-t_start)
    # print(analyzer_info["propagator_computation_time"])

   # pars = '_'.join([str(key)+"_"+str(value) for key, value in sorted(partitioner_hyperparams.items(), key=lambda kv: kv[0]) if key not in ["make_animation", "show_animation", "type"]])
   # pars2 = '_'.join([str(key)+"_"+str(value) for key, value in sorted(propagator_hyperparams.items(), key=lambda kv: kv[0]) if key not in ["input_shape", "type"]])
 
    error, avg_error = analyzer.get_error(input_constraint,output_constraint, t_max)

    # analyzer_info["save_name"] = img_save_dir+partitioner_hyperparams['type']+"_"+propagator_hyperparams['type']+"_"+pars+"_"+pars2+".png"
    # analyzer.visualize(input_range, output_range, show=False, show_legend=False, **analyzer_info)
    print('Average_error',avg_error )
    print('Final error',error )

    stats = {
       # "computation_time": t_end - t_start,
       # "propagator_computation_time": t_end - t_start,
        "output_range_estimate": output_constraint.range,
        "input_range": input_constraint.range,
        "propagator": type(analyzer.propagator).__name__,
        "partitioner": type(analyzer.partitioner).__name__,
        "final_error": error,
        "avg_error": avg_error,
        "time_steps": t_max,

       # "num_partitions": partitioner_hyperparams,

        # "neurons": ,
        # "activation": ,
    }
   # analyzer_info.pop("exact_hull", None)
   # analyzer_info.pop("estimated_hull", None)
    data_row = {**stats, **analyzer_info, **partitioner_hyperparams, **propagator_hyperparams}#, **model_info}
    return data_row

def add_approx_error_to_df(df):
    output_range_exact = get_exact_output_range(df)
    output_area_exact = np.product(output_range_exact[:,1] - output_range_exact[:,0])
    df['lower_bound_errors'] = ""
    df['output_area_estimate'] = ""
    df['output_area_error'] = ""
    for index, row in df.iterrows():
        lower_bnd_errors = output_range_exact[:,0] - row["output_range_estimate"][:,0]
        df.at[index, 'lower_bound_errors'] = lower_bnd_errors
        
        output_area_estimate = np.product(row["output_range_estimate"][:,1] - row["output_range_estimate"][:,0])
        df.at[index, 'output_area_estimate'] = output_area_estimate
        df.at[index, 'output_area_error'] = (output_area_estimate / output_area_exact) - 1.
        



def plot(df, stat):
    plt.rcParams['font.size'] = '20'
    output_range_exact = get_exact_output_range(df)
    for partitioner in df["partitioner"].unique():
        for propagator in df["propagator"].unique():
            if propagator == "EXACT" or partitioner == "EXACT":
                continue
            if partitioner == "UniformPartitioner":
                continue
            df_ = df[(df["partitioner"] == partitioner) & (df["propagator"] == propagator)]
            if propagator == "IBPAutoLIRPAPropagator" and partitioner == "SimGuidedPartitioner":
                linestyle = '--'
            else:
                linestyle = '-'

            plt.loglog(df_[stat].values, df_["error"],
                marker=algs[partitioner]["marker"],
                ms=8,
                color=cm.get_cmap("tab20c")(4*algs[propagator]["color_ind"]+algs[partitioner]["color_ind"]),
                label=algs[partitioner]["name"]+'-'+algs[propagator]["name"],
                linestyle=linestyle)

            # if propagator == "SDPPropagator" and partitioner == "SimGuidedPartitioner":
            #     pt = (df_[stat].values[0], df_["error"].values[0])
            #     text = (pt[0], pt[1]-0.1)
            #     plt.gca().annotate("Vanilla SDP\n(Fazlyab '19)", xy=pt,  xycoords='data',
            #                 xytext=text, textcoords='data',
            #                 arrowprops=dict(facecolor='black', shrink=0.05),
            #                 horizontalalignment='center', verticalalignment='top',
            #                 )

            # if propagator == "CROWNAutoLIRPAPropagator" and partitioner == "SimGuidedPartitioner":
            #     pt = (df_[stat].values[0], df_["error"].values[0])
            #     text = (pt[0], pt[1]-0.3)
            #     plt.gca().annotate("Vanilla CROWN\n(Zhang '18)", xy=pt,  xycoords='data',
            #                 xytext=text, textcoords='data',
            #                 arrowprops=dict(facecolor='black', shrink=0.05),
            #                 horizontalalignment='center', verticalalignment='top',
            #                 )

            # if propagator == "IBPAutoLIRPAPropagator" and partitioner == "SimGuidedPartitioner":
            #     pt = (df_[stat].values[2], df_["error"].values[2])
            #     text = (pt[0], pt[1]+1.)
            #     pt = (df_[stat].values[0], df_["error"].values[0])
            #     string = "All Blue Circles:\n(Xiang '20)"
            #     plt.gca().annotate(string, xy=pt,  xycoords='data',
            #                 xytext=text, textcoords='data',
            #                 arrowprops=dict(facecolor='black', shrink=0.05),
            #                 horizontalalignment='center', verticalalignment='top',
            #                 )
            #     pt = (df_[stat].values[1], df_["error"].values[1])
            #     plt.gca().annotate(string, xy=pt,  xycoords='data',
            #                 xytext=text, textcoords='data',
            #                 arrowprops=dict(facecolor='black', shrink=0.05),
            #                 horizontalalignment='center', verticalalignment='top',
            #                 )
            #     pt = (df_[stat].values[2], df_["error"].values[2])
            #     plt.gca().annotate(string, xy=pt,  xycoords='data',
            #                 xytext=text, textcoords='data',
            #                 arrowprops=dict(facecolor='black', shrink=0.05),
            #                 horizontalalignment='center', verticalalignment='top',
            #                 )
            #     plt.gca().text(text[0]+0.8, text[1]-0.8, "...", fontsize=30)

    plt.xlabel(stats[stat]["name"])
    plt.ylabel('Approximation Error')
    # plt.xlabel(stats[stat]["name"], fontsize=36)
    # plt.xticks(fontsize=36)
    # plt.ylabel('Approximation Error', fontsize=36)
    # plt.yticks(fontsize=36)
    # plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
    #    ncol=3, mode="expand", borderaxespad=0.)
    plt.tight_layout()
    plt.show()



def plot_errors(df, stat, model_params):
    for partitioner in df["partitioner"].unique():
        for propagator in df["propagator"].unique():
            if partitioner == "ClosedLoopUniformPartitioner":
                color ='green'
            elif partitioner == "ClosedLoopNoPartitioner":
                color='blue'
            else:
                color ='red'


            df_ = df[(df["partitioner"] == partitioner) & (df["propagator"] == propagator)]
            plt.plot(df_[stat] , df_["avg_error"], color=color,
                linestyle='solid', label=algs[partitioner]["name"]+'-'+algs[propagator]["name"]+'-'+'Average Error')   
            plt.yscale("log")      
            plt.plot(df_[stat] , df_["final_error"],  color=color,
                linestyle='dashed',label=algs[partitioner]["name"]+'-'+algs[propagator]["name"]+'-'+'Final Error')   

            plt.yscale("log")
         

    plt.xlabel(stats[stat]["name"])
    plt.ylabel('Approximation Error')
    plt.title(model_names[model_params['model_fn']])

    plt.legend(bbox_to_anchor=(0., 0.75, 0.45, .1), loc=4,
        ncol=1, borderaxespad=0.)    # plt.xlabel(stats[stat]["name"], fontsize=36)
    # plt.xticks(fontsize=36)
    # plt.ylabel('Approximation Error', fontsize=36)
    # plt.yticks(fontsize=36)
    # plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
    #    ncol=3, mode="expand", borderaxespad=0.)
    plt.tight_layout()
    plt.show()
algs ={
    "ClosedLoopNoPartitioner": {
        "name": "None",
    },
    "ClosedLoopUniformPartitioner": {
        "marker": "x",
        "color_ind": 0,
        "name": "Uniform",
    },
    "UnGuidedPartitioner": {
        "marker": "+",
        "color_ind": 0,
        "name": "Unguided",
    },
    "SimGuidedPartitioner": {
        "marker": "o",
        "color_ind": 0,
        "name": "SG",
    },
    "GreedySimGuidedPartitioner": {
        "marker": "^",
        "color_ind": 1,
        "name": "GSG",
    },
    "AdaptiveSimGuidedPartitioner": {
        "marker": "*",
        "color_ind": 2,
        "name": "AGSG",
    },
  
    "ClosedLoopIBPPropagator": {
        "color_ind": 0,
        "name": "IBP",
    },
    "ClosedLoopCROWNPropagator": {
        "color_ind": 1,
        "name": "CROWN",
    },
    "ClosedLoopFastLinPropagator": {
        "color_ind": 3,
        "name": "Fast-Lin",
    },
    "ClosedLoopSDPPropagator": {
        "color_ind": 2,
        "name": "SDP",
    },
    "relu": {
        "name": "ReLU",
    }
}

stats = {
    "propagator_computation_time": {
        "name": "Computation Time (Propagator Only) [s]"
    },
    "num_partitions": {
        "name": "Number of Partitions"
    },
    "num_propagator_calls": {
        "name": "Number of Propagator Calls"
    },
    "time_steps": {
        "name": "Time (sec)"
    },
}

names = {
    "lower_bnds": "Lower Bounds",
    "linf": "$\ell_\infty$-ball",
    "convex_hull": "Convex Hull",
}

citations = {
    "IBP": {
        "None": "\\cite{gowal2018effectiveness}",
        "SG": "\\cite{xiang2020reachable}",
    },
    "Fast-Lin": {
        "None": "\\cite{Weng_2018}",
    },
    "CROWN": {
        "None": "\\cite{zhang2018efficient}",
    },
    "SDP": {
        "None": "\\cite{fazlyab2019safety}",
    },
}

model_names= {
    "quadrotor": "Quadrotor",
    "double_integrator_mpc": "Double Integrator"



}

# def make_table(df):
#     partitioners = ["NoPartitioner", "UniformPartitioner", "SimGuidedPartitioner", "GreedySimGuidedPartitioner"]
#     propagators = ["IBPAutoLIRPAPropagator", "FastLinAutoLIRPAPropagator", "CROWNAutoLIRPAPropagator"]#, "SDPPropagator"]

#     neurons = df.model_neurons.iloc[0]
#     activation = df.model_activation.iloc[0]

#     print("\\begin{tabular}{c c| "+"c "*len(partitioners)+"}") 
#     print("\\hline \\multicolumn{"+str(2+len(partitioners))+"}{c}{Neurons: "+str(neurons)+" -- Activation: "+str(algs[activation]["name"])+"}\\\\ \\hline")
#     print("&& \\multicolumn{"+str(len(partitioners))+"}{c}{Partitioner} \\\\")
#     row = "&"
#     for partitioner in partitioners:
#         row += " & " + algs[partitioner]["name"]
#     print(row + " \\\\ \\hline")
#     print("\\multirow{"+str(len(propagators))+"}{*}{\\STAB{\\rotatebox[origin=c]{90}{Propagator}}}")
#     for propagator in propagators:
#         row = "& " + algs[propagator]["name"]
#         for partitioner in partitioners:
#             df_ = df[(df["partitioner"] == partitioner) & (df["propagator"] == propagator)]
#             stat = round(df_.error.to_numpy()[0], 3)
#             row += " & "
#             if partitioner == "NoPartitioner" or (propagator == "IBPAutoLIRPAPropagator" and partitioner in ["UniformPartitioner", "SimGuidedPartitioner"]):
#                 row += "\\cellcolor{Gray} "
#             row += str(stat)
#         print(row + " \\\\")
#     print("\\end{tabular}")

def table_single_model(df, partitioners, propagators, boundaries, neurons, name, activation):
    # print("\\multirow{"+str(len(propagators)*len(partitioners))+"}{*}{\\shortstack{"+name+" \\\\ "+str(neurons)+" \\\\ "+activation+"}} &")
    # print("\\multirow{"+str(len(propagators))+"}{*}{\\STAB{\\rotatebox[origin=c]{90}{Propagator}}}")
    for propagator in propagators:
        first = True
        for partitioner in partitioners:
            row = ""
            if first:
                row += "\\multirow{"+str(len(partitioners))+"}{*}{"+algs[propagator]["name"]+"} & "
                first = False
            else: row += " & "
            row += algs[partitioner]['name']
            if algs[propagator]['name'] in citations and algs[partitioner]['name'] in citations[algs[propagator]['name']]:
                row += "~"+citations[algs[propagator]['name']][algs[partitioner]['name']]
            for boundary in boundaries:
                df_ = df[(df["partitioner"] == partitioner) & (df["propagator"] == propagator) & (df["interior_condition"] == boundary)]
                stat = df_.error.mean()
                # stat = round(stat, 3)
                if math.isnan(stat):
                    stat = "-"
                else:
                    stat = '{:.2E}'.format(stat).lower()
                    stat = '\\num{'+stat+'}'
                row += " & "
                # if partitioner == "NoPartitioner" or (propagator == "IBPAutoLIRPAPropagator" and partitioner in ["UniformPartitioner", "SimGuidedPartitioner"]):
                #     row += "\\cellcolor{Gray} "
                row += str(stat)
        # if first: row = row[1:]; first = False
            print(row + " \\\\")
        print("\\hline")



if __name__ == '__main__':

    # Run an experiment
    # df = run_experiment()
    model_params = model_list[1]

    partitioners = ["None", "Uniform"]#, "GreedySimGuidedPartitioner", "AdaptiveSimGuidedPartitioner"]
    propagators = ["CROWN"]#, "SDP"]
    boundaries = ["linf"]#, "convex_hull", "lower_bnds"]
    experiments_list=["errorVstimeStep"  ] #"errorVsPartitions", 
    partitioner_hyperparams_to_use = {
            "None":
                {
                },
            "Uniform":
                {
                   # "num_partitions": [1,2,4,8,16,32,64,128]
                "num_partitions":  [np.array([4,4,1,1,1,1])],
               # "num_partitions": [np.array([4,4])],

                }

        }
    experiment_hyperparams = {
            "errorVsPartitions":
            {
            "t_max": [5], 

            },          
            "errorVstimeStep":

            {
            "t_max": [0.1,0.5,1.0,1.5,2.,2.5,3], #TODO: make it universerval for all systems
           # "t_max": range(1,11), #TODO: make it universerval for all systems

                },
        }
    # Make table
    print(experiment_hyperparams[ 'errorVstimeStep']['t_max'])
    df = collect_data_for_table(propagators,partitioners, experiments_list, experiment_hyperparams, model_params, boundaries)
   # plot_errors(df,"num_partitions")
    plot_errors(df,"time_steps", model_params)
   # print(df["final_error"], df["avg_error"])
    #for df_info in df:
        #plt.plot(df_info["partitons"], df_info["final_error"] )

    #print(df)
    # If you want to plot w/o re-running the experiments, comment out the experiment line.
    #if 'df' not in locals():
        # If you know the path
     #   latest_file = save_dir+"14-07-2020_18-56-40.pkl"

        # If you want to look up most recently made df
     #   list_of_files = glob.glob(save_dir+"/*.pkl")
    #    latest_file = max(list_of_files, key=os.path.getctime)

     #   df = pd.read_pickle(latest_file)

    print("\n --- \n")
    print("done!")

  #  make_table(df, partitioners, propagators, boundaries,)
   # make_big_table(df)

   # print("\n --- \n")
