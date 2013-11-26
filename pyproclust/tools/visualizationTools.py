'''
Created on 26/11/2013

@author: victor
'''
from pyproclust.clustering.cluster import Cluster
import numpy
from pyRMSD.RMSDCalculator import RMSDCalculator
from pyproclust.clustering.comparison.caDisplacement import CA_mean_square_displacement_of_cluster
import os
import matplotlib.cm as cm

def generate_CA_displacements_file(best_clustering, trajectoryHandler):
    global_cluster = Cluster(None, best_clustering["clustering"].get_all_clustered_elements())
    global_cluster.prototype = global_cluster.calculate_medoid(self.matrixHandler.distance_matrix)
    ca_pdb_coordsets =numpy.copy(trajectoryHandler.getJoinedPDB().select("name CA").getCoordsets())
    calculator = RMSDCalculator(calculatorType = "QTRFIT_SERIAL_CALCULATOR",
                                    fittingCoordsets = ca_pdb_coordsets)
    calculator.iterativeSuperposition()
    CA_mean_square_displacements= {
                                   "global":list(CA_mean_square_displacement_of_cluster(ca_pdb_coordsets,\
                                                                                        global_cluster))
                                   }
    clusters = best_clustering["clustering"].clusters
    for i in range(len(clusters)):
        cluster = clusters[i]
        # Pick the coordinates (ensuring that we are copying them)
        fitting_coordinates_of_this_cluster = ca_pdb_coordsets[cluster.all_elements]
        calculator = RMSDCalculator(calculatorType = "QTRFIT_SERIAL_CALCULATOR",
                                    fittingCoordsets = fitting_coordinates_of_this_cluster)

        # Make an iterative superposition (to get the minimum RMSD of all with respect to a mean conformation)
        calculator.iterativeSuperposition()

        # Calculate and convert to list (to serialize)
        CA_mean_square_displacements[cluster.id] = list(CA_mean_square_displacement_of_cluster(ca_pdb_coordsets,\
                                                                                               cluster))

    displacements_path = os.path.join(self.workspaceHandler["results"], "CA_displacements.json")

    return displacements_path, CA_mean_square_displacements

def calculate_bounding_box(coordinates, backbone_trace):
    coords = numpy.array(coordinates)
    [max_x,max_y,max_z] = numpy.max([numpy.max(numpy.max(coords,1),0).tolist()]+[numpy.max(backbone_trace,0).tolist()],0)
    [min_x,min_y,min_z] = numpy.min([numpy.min(numpy.min(coords,1),0).tolist()]+[numpy.min(backbone_trace,0).tolist()],0)
    center = numpy.array([min_x,min_y,min_z]) + ((numpy.array([max_x,max_y,max_z])-numpy.array([min_x,min_y,min_z])) /2.)
    return [[max_x, max_y, max_z],
            [max_x, max_y, min_z],
            [max_x, min_y, max_z],
            [max_x, min_y, min_z],
            [min_x, max_y, max_z],
            [min_x, max_y, min_z],
            [min_x, min_y, max_z],
            [min_x, min_y, min_z]], center.tolist()

def generate_CA_or_P_trace(trajectoryHandler):
    coordsets = numpy.array([])
    try:
        # Only get first frame of the selection
        coordsets = trajectoryHandler.getJoinedPDB().select("name CA P").getCoordsets()[0]
    except:
        print "[ERROR visualizationTools::generate_CA_or_P_trace] Impossible to get coordinates for trace"
    return coordsets.tolist()

def generate_selection_centers_file(parameters, best_clustering, workspaceHandler, trajectoryHandler):
    # TODO: Superpose and center coords (or getting already superposed confs)
    #########################

    #########################
    centers_path = os.path.join(workspaceHandler["results"], "selection_centers.json")
    clustering = best_clustering["clustering"]
    ligand_coords = trajectoryHandler.getSelection(parameters["matrix"]["parameters"]["body_selection"])

    centers_contents={}
    centers = []

    # Calculate trace
    centers_contents["backbone_trace"] = generate_CA_or_P_trace(trajectoryHandler)

    # Get Bounding Box
    centers_contents["bounding_box"] , centers_contents["bounding_box_center"] = calculate_bounding_box(
                                                                                                        ligand_coords.tolist() ,
                                                                                                        centers_contents["backbone_trace"])

    # Colors iterator
    colors = iter(cm.rainbow(numpy.linspace(0, 1, len(clustering.clusters))))

    # calculate per cluster centers for selection ( and prototype center)
    centers_contents["points"] = {}
    for cluster in clustering.clusters:
        centers = []
        for element in cluster.all_elements:
            coords = ligand_coords[element]
            centers.append(list(coords.mean(0)))
        centers_contents["points"][cluster.id] = {}
        centers_contents["points"][cluster.id]["prototype"] = list(ligand_coords[cluster.prototype].mean(0))
        centers_contents["points"][cluster.id]["centers"] = centers
        centers_contents["points"][cluster.id]["color"] = list(next(colors))[0:3]

    return centers_path, centers_contents