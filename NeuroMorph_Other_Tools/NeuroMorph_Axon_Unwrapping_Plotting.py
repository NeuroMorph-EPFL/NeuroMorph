 ### for debugging in Blender
# sys.path.append('/home/anne/Desktop/NeuroMorph')
# from NeuroMorph_Axon_Unwrapping import *


# python3
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import imp


# # To run from console
# import imp
# import NeuroMorph_Plotting as nmp
# nmp.main()
# imp.reload(nmp)
# nmp.main()


nsynapse = 0  # hard-coded options: 0,1,2
bdry_vscls_only = True
dist_to_bdry = .060
dist_to_bdry2 = .075
plot_both_dists = True
plot_jitter = False

def rand_jitter(arr):
    stdev = .01*(max(arr)-min(arr))
    return arr + np.random.randn(len(arr)) * stdev

def get_xy(bdry_vscls_only, dist_to_bdry, vscl_coords):
	if bdry_vscls_only:
		vscl_coords_close = [[[x,y],d] for [[x,y],d] in vscl_coords if d < dist_to_bdry]
		vscl_coords = vscl_coords_close

	xs = [x for [[x,y],d] in vscl_coords]
	ys = [y for [[x,y],d] in vscl_coords]
	dists = [d for [[x,y],d] in vscl_coords]

	maxd = max(dists)
	mind = min(dists)
	# dists_scl =  [(d-mind)/(maxd-mind) for d in dists]
	dists_scl =  [d/maxd for d in dists]
	dists_as_color = [[0, min(1,2*(1-d)), min(1,2*d)] for d in dists_scl]
	return(xs, ys, dists_as_color)


def main():

	# File names
	path = "/home/anne/Desktop/NeuroMorph/"
	this_axon = ""  # cholinergic2_
	bdry_pt_name = "xsection_bdries_for_plotting.p"
	vscl_coord_name = "vscl_coords_for_plotting.p"
	syn_coord_name = "syn_coords_for_plotting.p"

	# Locations of cross-section boundary vertices
	# bdry_pt_coords = pickle.load(open("/home/anne/Desktop/NeuroMorph/xsection_bdries_for_plotting.p", "rb"))
	bdry_pt_coords = pickle.load(open(path+this_axon+bdry_pt_name, "rb"))
	all_xs = []
	all_ys = []
	for cind in range(0,len(bdry_pt_coords)):
		xs = [x for [x,y] in bdry_pt_coords[cind]]
		ys = [y for [x,y] in bdry_pt_coords[cind]]
		all_xs = all_xs + xs
		all_ys = all_ys + ys

	plt.subplot(1, 3, 1)
	plt.scatter(all_xs, all_ys, s=1, c=[.4,.4,.4])  # c='g'
	plt.title("Cross-section boundary vertices")

	xlim = [min(all_xs)-.1, max(all_xs)+.1]
	ylim = [min(all_ys)-.1, max(all_ys)+.1]
	axes = plt.gca()
	axes.set_xlim(xlim)
	axes.set_ylim(ylim)
	# plt.show()


	# Projections of vesicles onto the boundary vertices
	# vscl_coords = pickle.load(open("/home/anne/Desktop/NeuroMorph/vscl_coords_for_plotting.p", "rb"))
	vscl_coords = pickle.load(open(path+this_axon+vscl_coord_name, "rb"))

	xs, ys, dists_as_color = get_xy(bdry_vscls_only, dist_to_bdry, vscl_coords)
	plot2_title = "Projections of vesicles onto boundary vertices within " + str(dist_to_bdry)


	if plot_both_dists:
		xs2, ys2, dists_as_color2 = get_xy(bdry_vscls_only, dist_to_bdry2, vscl_coords)
		dists_as_color = dists_as_color2  # use same scale
		plot3_title = "Projections of vesicles onto boundary vertices within " + str(dist_to_bdry2)

	elif plot_jitter:
		x_jitt = rand_jitter(xs)
		y_jitt = rand_jitter(ys)
		xs2 = x_jitt
		ys2 = y_jitt
		dists_as_color2 = dists_as_color
		plot3_title = "Projections of vesicles with added jitter"



	# Projections of synapse vertices onto the boundary vertices
	syn_color = [1,.4,.4]
	if nsynapse >= 1:
		# syn_coords = pickle.load(open("/home/anne/Desktop/NeuroMorph/syn_coords_for_plotting.p", "rb"))
		syn_coords = pickle.load(open(path+this_axon+syn_coord_name, "rb"))
		xs_syn = [x for [[x,y],d] in syn_coords]
		ys_syn = [y for [[x,y],d] in syn_coords]

		if nsynapse >=2:
			syn_coords2 = pickle.load(open(path+this_axon+"syn_coords_for_plotting 1.p", "rb"))
			xs_syn2 = [x for [[x,y],d] in syn_coords2]
			ys_syn2 = [y for [[x,y],d] in syn_coords2]


	plt.subplot(1, 3, 2)

	if nsynapse >= 1:
		plt.scatter(xs_syn, ys_syn, s=70, linewidths=0, alpha=.25, c=syn_color)
		if nsynapse >= 2:
			plt.scatter(xs_syn2, ys_syn2, s=70, linewidths=0, alpha=.25, c=syn_color)

	plt.scatter(xs, ys, s=35, linewidths=0, alpha=.5, c=dists_as_color)
	plt.title(plot2_title)
	axes = plt.gca()
	axes.set_xlim(xlim)
	axes.set_ylim(ylim)


	# Projections of vesicles with added jitter
	plt.subplot(1, 3, 3)

	if nsynapse >= 1:
		plt.scatter(xs_syn, ys_syn, s=70, linewidths=0, alpha=.25, c=syn_color)
		if nsynapse >= 2:
			plt.scatter(xs_syn2, ys_syn2, s=70, linewidths=0, alpha=.25, c=syn_color)

	plt.scatter(xs2, ys2, s=35, linewidths=0, alpha=.5, c=dists_as_color2)
	plt.title(plot3_title)
	axes = plt.gca()
	axes.set_xlim(xlim)
	axes.set_ylim(ylim)
	# plt.legend(dists)
	# plt.colorbar()


	# Add a legend hack
	red_patch = mpatches.Patch(color=syn_color, label='Synapse')
	green_patch = mpatches.Patch(color=[0,1,0], label='Distance 0')
	blue_patch = mpatches.Patch(color=[0,0,1], label='Distance max')
	if nsynapse >= 1:
		plt.legend(handles=[red_patch,green_patch,blue_patch])
	else:
		plt.legend(handles=[green_patch,blue_patch])


	plt.show()



	# plt.plot(dists, 'o')



