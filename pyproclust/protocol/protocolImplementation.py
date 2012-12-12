'''
Created on 21/05/2012

@author: victor
'''
import time
from pyRMSD.matrixHandler import MatrixHandler

import pyproclust.tools.commonTools as common
import pyproclust.tools.scriptTools as scripts_common
from pyproclust.clustering.comparison.comparator import Separator,\
    ClusteringStatisticalAnalyzer, ClusteringPlotsGenerator
from pyproclust.clustering.selection.bestClusteringSelector import BestClusteringSelector
from pyproclust.protocol.workspaceHandler import WorkspaceHandler
from pyproclust.protocol.trajectoryHandler import TrajectoryHandler 
from pyproclust.protocol.clusteringExplorationFunctions import do_clustering_exploration
from pyproclust.protocol.protocolImplementationFunctions import get_algorithm_scheduler,\
    save_results, save_most_representative, do_clustering_filtering,\
    clustering_scoring
from pyproclust.protocol.refinementProtocol import pureRefinementProtocol,\
    mixedRefinementProtocol
from pyproclust.clustering.clusterization import Clustering
from pyproclust.tools.plotTools import matrixToImage
from pyproclust.htmlreport.htmlReport import HTMLReport
from pyproclust.tools.scriptTools import classify_generated_clusterings
from pyproclust.clustering.comparison.distrprob.kullbackLieblerDivergence import KullbackLeiblerDivergence
from pyproclust.tools.pdbTools import get_number_of_frames
#from pyproclust.protocol.serialProcessPool import SerialProcessPool


class Protocol(object):

    def __init__(self):
        self.htmlReport = HTMLReport()
        
    def run(self,protocol_params):
        
        #####################
        # Create workspace 
        #####################
        self.workspaceHandler = WorkspaceHandler(protocol_params)
        self.workspaceHandler.create_directories()
        
        #####################
        # Start timing 
        #####################
        global_time_start = time.time()

        #####################
        # Loading trajectory 
        #####################
        self.trajectoryHandler = TrajectoryHandler(protocol_params.pdb1, protocol_params.pdb2, protocol_params.rmsd_selection)
        self.htmlReport.report["Trajectories"] = self.trajectoryHandler
        
        ##############################
        # Obtaining the distance matrix
        ##############################
        time_start = time.time()
        self.matrixHandler = MatrixHandler(self.workspaceHandler.matrix_path)
        
        if protocol_params.shallWeCalculateDistanceMatrix():
            
            self.matrixHandler.createMatrix(self.trajectoryHandler.coordsets)
            
            if protocol_params.store_matrix_path != None:
                matrix_complete_path = self.workspaceHandler.matrix_path +"/"+protocol_params.store_matrix_path
                self.matrixHandler.saveMatrix(matrix_complete_path)
                time_end = time.time()
                self.htmlReport.report["Timing"] +='Creating and saving the matrix took %0.3f s\n' % (time_end-time_start)
            else:
                time_end = time.time()
                self.htmlReport.report["Timing"] +='Creating the matrix took %0.3f s\n' % (time_end-time_start)
        else:
            matrix_complete_path = self.workspaceHandler.matrix_path +"/"+protocol_params.matrix_file
            common.print_and_flush( "We don't need to calculate the distance matrix because it is provided in: " +matrix_complete_path+"\n")
            self.matrixHandler.loadMatrix(matrix_complete_path)
            time_end = time.time()
            self.htmlReport.report["Timing"] += 'Loading the matrix took %0.3f s\n' % (time_end-time_start)
        
        self.htmlReport.report["Matrix Handler"] = self.matrixHandler
        ############################################
        # Distribution analysis
        ############################################
        if protocol_params.shallWeCompareTrajectories():
            common.print_and_flush("Calculating rmsd distributions and KL divergence...")
            time_end = time.time()
            klDiv = KullbackLeiblerDivergence(protocol_params.pdb1,\
                                              protocol_params.pdb2,\
                                              get_number_of_frames(protocol_params.pdb1),
                                              get_number_of_frames(protocol_params.pdb2),
                                              self.matrixHandler.distance_matrix)
            
            klDiv.plot_distributions(self.workspaceHandler.matrix_path+"/rmsd_distrib")
            klDiv.save_to_file(self.workspaceHandler.matrix_path+"/rmsd_distrib")
            
            self.htmlReport.report["KL"] = klDiv
            self.htmlReport.report["Timing"] += 'Calculating RMSDs distribution and KL Divergence took %0.3f s\n' % (time_end-time_start)
            common.print_and_flush(" Done\n")
        
        #########################
        # Matrix plot
        #########################
        matrixToImage(self.matrixHandler.distance_matrix,self.workspaceHandler.matrix_path+"/matrix_plot.png")
        
        ############################
        # Clustering exploration
        ############################
        time_start = time.time()
        do_clustering_exploration(protocol_params, get_algorithm_scheduler(protocol_params),\
                                        self.matrixHandler.distance_matrix,\
                                        self.matrixHandler.max_dist, self.matrixHandler.mean_dist,\
                                        self.workspaceHandler.clusterings_path, self.htmlReport)
        time_end = time.time()
        self.htmlReport.report["Timing"] += 'Clustering generation took %0.3f s\n' % (time_end-time_start)
                
        ####################################
        # Load created clusterings from disk
        ####################################
        time_start = time.time()
        non_filtered_clusterings = Clustering.load_all_from_directory(self.workspaceHandler.clusterings_path)
        time_end = time.time()
        self.htmlReport.report["Timing"] += 'Clustering loading took %0.3f s\n' % (time_end-time_start)
        tags = ['Spectral', 'DBSCAN', 'GROMOS', 'K-Medoids', 'Random', 'Hierarchical']
        counter  = Clustering.classify(tags, clusterings = non_filtered_clusterings)  
        number_of_tries = len(non_filtered_clusterings)
        self.htmlReport.report["Tries"]["Contents"]["Number of tries"] = number_of_tries
        self.htmlReport.report["Tries"]["Contents"]["All Clusterings"] = (tags, counter)
        
        ######################
        # First filtering
        ######################
        time_start = time.time()
        filtered_clusters, not_selected_clusterings = do_clustering_filtering(non_filtered_clusterings,protocol_params,non_filtered_clusterings,self.trajectoryHandler.number_of_conformations)
        self.htmlReport.report['Tries']["KO Clusterings"] = list(not_selected_clusterings)
        self.htmlReport.report['Tries']["OK Clusterings"] = list(filtered_clusters)
        self.htmlReport.report["Timing"] += 'Filtering took %0.3f s\n' % (time_end-time_start)
        
        if len(filtered_clusters) == 0:
            common.print_and_flush( "The clustering search gave no clusterings. Relax noise or num. of clusters parameters.")
            common.print_and_flush( "Exiting...\n")
        else:      
            ######################
            # Clustering scoring
            ######################
            time_start = time.time()
            string_results, results_pack = clustering_scoring(filtered_clusters,protocol_params,self.matrixHandler.distance_matrix,\
                                                              self.trajectoryHandler.pdb_structure)
            time_end = time.time()
            self.htmlReport.report["Timing"] += 'Clustering scoring took %0.3f s\n' % (time_end-time_start)

            ######################
            # Bake up results
            ######################
            save_results(protocol_params,self.workspaceHandler.results_path,string_results,results_pack)
            self.htmlReport.report["Evaluations"] = results_pack
#            result_pack_file_handler = open(self.workspaceHandler.results_path+"/"+protocol_params.report_file+".bin","r")
#            results_pack = pickle.load(result_pack_file_handler)
#            result_pack_file_handler.close()
            ######################
            # Choose the best one
            ######################
            bestClusterSelector = BestClusteringSelector( protocol_params.cluster_score_value_map)
            (best_score, best_clustering), all_scores = bestClusterSelector.chooseBestClustering(results_pack)
            best_cluster_string = "Best clustering has a normalized score of : %.4f Details: %s Number of Clusters: %d\n"%(best_score,best_clustering.details,len(best_clustering.clusters))
            common.print_and_flush( best_cluster_string)
            self.htmlReport.report["Scores"] = all_scores
            self.htmlReport.report["Best Clustering Selection"] = (best_score, best_clustering)
            
            ######################
            # Refine results
            ######################
            if protocol_params.do_refinement:
                ## Change params
                old_min = protocol_params.min_clusters
                old_max = protocol_params.max_clusters
                old_kmedoids_step = protocol_params.kmedoids_step
                old_spectral_step = protocol_params.spectral_clustering_step
                protocol_params.max_clusters = protocol_params.refinement_max_clusters
                protocol_params.kmedoids_step = protocol_params.refinement_step
                protocol_params.spectral_clustering_step = protocol_params.refinement_step
                
                separator = Separator()
                pure_A , pure_B, mixed_with_elements = separator.separate(best_clustering, protocol_params.pdb1, protocol_params.pdb2)
                pre_refinement_cluster_lengths = {}
                pre_refinement_cluster_lengths['pure_A'] = len(pure_A)
                pre_refinement_cluster_lengths['pure_B'] = len(pure_B)
                pre_refinement_cluster_lengths['mixed'] = len(mixed_with_elements)
                
                print "[refinement] Initial params, max_clusters: ", protocol_params.max_clusters,"step: ",protocol_params.kmedoids_step
                print "[refinement] Initial clusters A: %d B: %d Mixed:%d"%(len(pure_A),len(pure_B),len(mixed_with_elements)) 
                
                new_clusters = []
                post_refinement_cluster_lenghts = {}
                
                new_pure_A = None
                if len(pure_A) != 0:
                    print "[refinement] Refining A"
                    protocol_params.min_clusters = max(protocol_params.refinement_min_clusters,len(pure_A))
                    print "[refinement] Refining A. protocol_params.min_clusters changed from %d to %d"%(old_min,protocol_params.min_clusters)
                    refiner = pureRefinementProtocol(pure_A, self.matrixHandler.distance_matrix,\
                                                     self.workspaceHandler.refinement_pure_A+'/clusterings',\
                                                     self.trajectoryHandler.pdb_structure)
                    new_pure_A = refiner.run(protocol_params)
                    if new_pure_A != None:
                        new_clusters.extend(new_pure_A)
                        post_refinement_cluster_lenghts['pure_A'] = len(new_pure_A)
                        print "[refinement] A has been refined. Clusters changed from %d to %d"%(len(pure_A),len(new_pure_A))
                    else:
                        print "[refinement] Impossible to refine A"
                else:
                    print "[refinement] No clusters in A, impossible to refine."
                
                if new_pure_A == None:
                    new_clusters.extend(pure_A)
                    post_refinement_cluster_lenghts['pure_A'] = pre_refinement_cluster_lengths['pure_A']
                
                new_pure_B = None   
                if len(pure_B) != 0:
                    print "[refinement] Refining B"
                    protocol_params.min_clusters = max(protocol_params.refinement_min_clusters,len(pure_B))
                    print "[refinement] Refining B. protocol_params.min_clusters changed from %d to %d"%(old_min,protocol_params.min_clusters)
                    refiner = pureRefinementProtocol(pure_B, self.matrixHandler.distance_matrix,\
                                                     self.workspaceHandler.refinement_pure_B+'/clusterings',\
                                                     self.trajectoryHandler.pdb_structure)
                    new_pure_B = refiner.run(protocol_params)
                    if new_pure_B != None:
                        new_clusters.extend(new_pure_B)
                        post_refinement_cluster_lenghts['pure_B'] = len(pure_B)
                        print "[refinement] B has been refined. Clusters changed from %d to %d"%(len(pure_B),len(new_pure_B))
                    else:
                        print "[refinement] Impossible to refine B"
                else:
                    print "[refinement] No clusters in B, impossible to refine."
                    
                if new_pure_B == None:
                    new_clusters.extend(pure_B)
                    post_refinement_cluster_lenghts['pure_B'] = pre_refinement_cluster_lengths['pure_B']
                
                new_mixed_clusters = None
                if len(mixed_with_elements) != 0:
                    print "[refinement] Refining Mixed"
                    protocol_params.min_clusters = max(protocol_params.refinement_min_clusters,len(mixed_with_elements))
                    print "[refinement] Refining Mixed. protocol_params.min_clusters changed from %d to %d"%(old_min,protocol_params.min_clusters)
                    
                    refiner = mixedRefinementProtocol(mixed_with_elements, self.matrixHandler.distance_matrix,\
                                                     self.workspaceHandler.refinement_mixed+'/clusterings',\
                                                     self.trajectoryHandler.pdb_structure)
                    new_mixed_clusters = refiner.run(protocol_params)
                    if new_mixed_clusters != None:
                        new_pure_A, new_pure_B, new_mixed = new_mixed_clusters
                        new_clusters.extend(new_mixed)
                        new_clusters.extend(new_pure_A)
                        new_clusters.extend(new_pure_B)
                        post_refinement_cluster_lenghts['mixed'] = len(new_mixed)
                        post_refinement_cluster_lenghts['mixed_pure_A'] = len(new_pure_A)
                        post_refinement_cluster_lenghts['mixed_pure_B'] = len(new_pure_B)
                        print "[refinement] Mixed has been refined. Clusters changed from %d to %d"%(len(mixed_with_elements),len(new_mixed))
                    else:
                        print "[refinement] Impossible to refine B"
                else:
                    print "[refinement] No clusters in B, impossible to refine." 
                  
                if new_mixed_clusters == None:
                    only_mixed = []
                    for pack in mixed_with_elements:
                        only_mixed.append(pack[0])
                    new_clusters.extend(only_mixed )
                    post_refinement_cluster_lenghts['mixed'] = pre_refinement_cluster_lengths['mixed']
                    post_refinement_cluster_lenghts['mixed_pure_A'] = 0
                    post_refinement_cluster_lenghts['mixed_pure_B'] = 0
                
                open(self.workspaceHandler.results_path+"/refinement.txt","w").write("""pure A: %d -> %d
pure B: %d -> %d
mixed: %d -> %d
new pure A in mixed: %d
new pure B in mixed: %d\n"""%(pre_refinement_cluster_lengths["pure_A"],post_refinement_cluster_lenghts["pure_A"],\
                         pre_refinement_cluster_lengths["pure_B"],post_refinement_cluster_lenghts["pure_B"],\
                         pre_refinement_cluster_lengths["mixed"],post_refinement_cluster_lenghts["mixed"],\
                         post_refinement_cluster_lenghts['mixed_pure_A'],post_refinement_cluster_lenghts['mixed_pure_B']))
                
                best_clustering = Clustering(new_clusters, "Refined")
                all_elems = []
                for c in best_clustering.clusters:
                    all_elems.extend(c.all_elements)
                
                ## Restore params
                protocol_params.max_clusters = old_max
                protocol_params.kmedoids_step = old_kmedoids_step
                protocol_params.spectral_clustering_step = old_spectral_step
            
            #########################
            # Get statistics etc...
            #########################
            if protocol_params.most_representative_pdb_file != "":
                save_most_representative(protocol_params,best_clustering,\
                                        self.matrixHandler.distance_matrix,\
                                        self.workspaceHandler.tmp_path,\
                                        self.workspaceHandler.results_path)
            
            
            analyzer = ClusteringStatisticalAnalyzer(best_clustering,\
                                                     protocol_params.pdb1,\
                                                     protocol_params.pdb2,\
                                                     self.matrixHandler.distance_matrix,\
                                                     protocol_params.shallWeCompareTrajectories())
            analyzer.per_cluster_analytics()
            
            analyzer.per_clustering_analytics()
            
            plotGenerator = ClusteringPlotsGenerator(analyzer)
            
            big_plot = plotGenerator.generate_and_compose_big_plot(composition_size= (1024,720), max_radius = 150, ball_horizontal_separation = 50, ball_vertical_separation = 100)
            
            if protocol_params.shallWeCompareTrajectories():
                small_plot = plotGenerator.generate_and_compose_small_plot(composition_size= (400,700))
            else:
                small_plot = plotGenerator.generate_and_compose_small_plot(composition_size= (400,300))
            
            big_plot.save(self.workspaceHandler.results_path+"/analysis_plot_big.png")
            small_plot.save(self.workspaceHandler.results_path+"/analysis_plot_small.png")
            
        global_time_end = time.time()
        self.htmlReport.report["Timing"] += 'All the process took %0.3f s\n' % (global_time_end-global_time_start)
        
        time_file = open(self.workspaceHandler.tmp_path+"/timing.txt","w")
        time_file.write(self.htmlReport.report["Timing"])
        time_file.close()
        
        
        #HTML REPORT
        html_file = open(self.workspaceHandler.results_path+"/report.html","w")
        html_file.write(self.htmlReport.generateHTML())
        html_file.close()
        
        #IMAGES FOR REPORT
        self.htmlReport.report["Image Paths"]["kl"] = self.workspaceHandler.matrix_path+"/rmsd_distrib.png"
        self.htmlReport.report["Image Paths"]["matrix"] = self.workspaceHandler.matrix_path+"/matrix_plot.png"
        self.htmlReport.report["Image Paths"]["clustering_small"] = self.workspaceHandler.results_path+"/analysis_plot_small.png"
        self.htmlReport.report["Image Paths"]["clustering_big"] = self.workspaceHandler.results_path+"/analysis_plot_big.png"
        self.htmlReport.create_thumbnails(self.workspaceHandler.results_path)
        
    