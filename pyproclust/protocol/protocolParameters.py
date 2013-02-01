'''
Created on 04/06/2012

@author: victor
'''

class ProtocolParameters():
    
    @classmethod
    def get_default_params(cls):
        return {
                "control":{
                    "number_of_processors":1,
                    "algorithm_scheduler_sleep_time":15,
                    "scoring_scheduler_sleep_time":15
                },
                "workspace":{
                             "base": ".",
                             "results": "/results",
                             "tmp": "/tmp",
                             "clusterings": "/clusterings",
                             "refinement":{
                                           "pure_A":"/pure_A",
                                           "pure_B":"/pure_B",
                                           "mixed":"/mixed"
                              }
                },
                "matrix":{
                            "action": None, 
                            "matrix_path": None,
                            "save_matrix": None,
                            "store_matrix_path" : None,
                            "pdb1": None,
                            "pdb2": None,
                            "fit_selection": "name CA",
                            "rmsd_selection":"name CA"
                },
                "algorithms":{
                             "gromos":{
                                       "use": None,
                                       "auto": None,
                                       "parameters":[
                                                 {
                                                    "cutoff": None
                                                 }
                                        ]
                              },
                              "spectral":{
                                       "use": None,
                                       "auto": None,
                                       "parameters":[
                                                 {
                                                     "sigma": None,
                                                     "k": None,
                                                     "use_k_medoids": None
                                                 }
                                        ]
                              },
                              "dbscan":{
                                       "use": None,
                                       "auto": None,
                                       "parameters":[
                                                 {
                                                     "eps": None,
                                                     "minpts": None
                                                 }
                                        ]
                              },
                              "hierarchical":{
                                       "use": None,
                                       "auto": None,
                                       "parameters":[
                                                 {
                                                     "cutoff": None,
                                                     "method": None
                                                 }
                                        ]
                              },
                              "kmedoids":{
                                       "use": None,
                                       "auto": None,
                                       "parameters":[
                                                 {
                                                     "k": None,
                                                     "seeding_type": None,
                                                     "seeding_max_cutoff": None
                                                 }
                                                 ]
                              },
                              "random":{
                                       "use": None,
                                       "auto": None,
                                       "parameters":[
                                                 {
                                                    "num_clusters": None,
                                                    "max_num_of_clusters": None
                                                 }
                                                 ]
                              }
                },
                "evaluation":{
                              "maximum_noise": None,
                              "minimum_clusters": None,
                              "maximum_clusters": None,
                              "minimum_cluster_size":None,
                              "query_types":[],
                              "evaluation_criteria":[]
                },
                "refinement":{
                              "use": None,
                              "step": None,
                              "minimum_clusters":None,
                              "maximum_clusters":None
                },
                "results":{
                           
                }
        }
    
    """
    Stores parameters for values 
    """
    def __init__(self, params_dic):
        self.params_dic = params_dic
#         ######################
#         # Global parameters
#         ######################
#         self.number_of_processors = 1   # Maximum number of processors to be used by the protocol
#         self.algorithm_scheduler_sleep_time = 15
#         self.scoring_scheduler_sleep_time = 15
#         
#         ######################
#         # Workspace related stuff
#         ######################
#         self.working_directory ="."
#         self.__workspace = {}
#         self.__workspace["results"] = "/results"
#         self.__workspace["tmp"] = "/tmp"
#         self.__workspace["matrix analysis"] = "/matrix"
#         self.__workspace["clusterings"] = "/clusterings"
#         self.__workspace["refinement_base"] = "/refinement"
#         self.__workspace["pure_A"] = "/pure_A"
#         self.__workspace["pure_B"] = "/pure_B"
#         self.__workspace["mixed"] = "/mixed"
#         self.__workspace_allowed_items = self.__workspace.keys()
#         
#         ######################
#         # Related to the distance matrix
#         # loading / creation
#         ######################
#         self.matrix_path = None
#         self.pdb1=None
#         self.pdb2=None
#         #self.CA_simplification = True
#         self.store_matrix_path = None
#         self.fit_selection = "name CA"
#         self.rmsd_selection ="name CA"
#         
#         ######################
#         # Details of the algorithms
#         ######################
#         self.use_gromos = False
#         self.use_kmedoids = False
#         self.use_random = False
#         self.use_hierarchical = False
#         self.use_spectral = False
#         self.use_dbscan = False
#         self.gromos_cutoff_list = []
#         self.hierarchical_cutoff_list = []
#         self.hierarchical_cutoff_refinement_value = 200
#         self.max_random_clusters = 0
#         self.kmedoids_step = 2
#         self.spectral_clustering_step = 2
#         self.dbscan_param_pairs = [] # (minpts, cutoff) tuples
#         
#         ######################
#         # User preferences
#         ######################
#         self.min_clusters = 1
#         self.max_clusters = 100
#         self.max_noise = 20 # 20%
#         self.min_cluster_size = 10 # Every cluster below this size will be considered noise
#         self.do_refinement = False
#         self.refinement_min_clusters = 5
#         self.refinement_max_clusters = 100
#         self.refinement_step = 5
#        
#         ########################
#         # Results
#         ########################
#         self.report_file = ""
#         self.most_representative_pdb_file = ""
#         
#         ########################
#         # Cluster scoring
#         ########################
#         self.evaluation_types = []
#         self.query_types = []
#         self.cluster_score_value_map = {} # This dictionary is indexed by analysis name
#         # and for each analysis name it has a weight. Is important that, if we want to have
#         # our result between 0 and 1, that the weights sum exactly the number of keys.
#         # i.e {"cohesion":0.75,"separation":1.25} In this case the cohesion value is less important
#         # in the scoring.
#         
#         #########################
#         # Trajectory comparison
#         #########################
#         self.state_graph_path = ""
        
    
    def shallWeMergetrajectories(self):
        return self.pdb2 != None
    
    def getWorkspacePathFor(self,item,add_working_dir=True):
        """
        Recreates the path into the workspace for one of the required folders.
        """
        if item in self.__workspace_allowed_items:
            if not add_working_dir:
                return self.__workspace[item]
            else:
                return self.working_directory+self.__workspace[item]
        else:
            print "Available items are: ",self.__workspace_allowed_items
    
    def setWorkspacePathFor(self,item, folder_name):
        """
        Sets the path into workspace for one of the required folders.
        """
        if item in self.__workspace_allowed_items:
            self.__workspace[item] = folder_name
        else:
            print "Available items are: ",self.__workspace_allowed_items    
    
            
