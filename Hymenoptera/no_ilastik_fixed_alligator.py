import h5py
import skfmm
import time
import numpy as np
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
#matplotlib.use('Agg')
#import cv2
from scipy import ndimage as ndi
from skimage.morphology import watershed
from skimage.feature import peak_local_max
import scipy.ndimage
from scipy import ndimage
from mpi4py import MPI
import pims
from PIL import Image
import glob

rad_tol = 30

# def rgb2gray(rgb):
# 	r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
# 	gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
# 	return gray

def rgb2gray(rgb):
	r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
	gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
	return 1-gray

def setup(w,sd):
	a=2


def read_in_frame(filename):
	im = Image.open(filename)
	imarray = np.array(im)
	#imarray = rgb2gray(imarray)
	imarray = scipy.ndimage.filters.gaussian_filter(imarray,0.5)
	print np.shape(imarray)
	# plt.imshow(1-imarray,cmap='hot')
	# plt.show()
	#gray = rgb2gray(imarray)
	dim1,dim2 = np.shape(imarray)#np.shape(gray)
	data = np.zeros((dim1,dim2))
	for i in xrange(dim1):
		for j in xrange(dim2):
			data[i][j] = 1-imarray[i][j]
	data += np.abs(np.amin(data))
	# plt.imshow(data/np.amax(data),cmap='hot')
	# plt.show()
	return data/np.amax(data)

def pre_process(slice1,slice2):
	(d1,d2) = np.shape(slice1)
	print 'd1 is: ' , d1
	print 'd2 is: ', d2
	for i in xrange(int(d1)):
		for j in xrange(int(d2)):
			if int(slice1[i][j]) == int(1) and int(slice2[i][j]) == int(1):
				slice1[i][j] = 0
	return slice1,slice2

def expand(i,j,tmp3,dx,dy):
	toreturn=[]
	if i < (dx-1) and tmp3[i+1][j] == 0:
		toreturn.append((i+1,j))
	if j<(dy-1) and tmp3[i][j+1] == 0:
		toreturn.append((i,j+1))
	if i > 0 and tmp3[i-1][j] == 0:
		toreturn.append((i-1,j))
	if j > 0 and tmp3[i][j-1] == 0:
		toreturn.append((i,j-1))
	return toreturn

def segmentation3(filename,cx,cy,dx,dy,dz,times,m):
	iterator = 0 
	file_counter = 0
	x = np.arange(0, dy)
	y = np.arange(0, dx)
	X, Y = np.meshgrid(x, y)
	tmp = np.zeros((dx,dy))
	print 'Initilializing'
	shuffler = range(len(cx))
	shuffler = np.random.permutation(shuffler)
	for i in xrange(len(cx)):
		#tmp[cy[shuffler[i]]][cx[shuffler[i]]] = i+1
		tmp[cy[i]][cx[i]] = shuffler[i]+1
	plt.imshow(tmp,cmap='hot')
	plt.title('tmp')
	plt.show()
	plt.savefig('./33.png', dpi=300,bbox_inches='tight')
	plt.clf()
	todo = []
	for i in xrange(len(cx)):
		todo.append(expand(int(cy[i]),int(cx[i]),tmp,dx,dy))
	print 'made to do'
	tmin= np.amin(times)
	tmax= np.amax(times)
	t = 0
	dt = 0.025*4
	while t< tmax+1:
		tmp2 = np.copy(tmp)
		#for i in xrange(len(todo)):
		#	print todo[i]
		lens = [ len(list(set(todo[i]))) for i in xrange(len(todo))]
		#print lens
		tmp_list = [[] for i in xrange(len(cx))]
		shuffler_for_order = range(len(cx))
		shuffler_for_order = np.random.permutation(shuffler_for_order)
		for ii in range(len(cx)):
			i = shuffler_for_order[ii]
			#print todo[i]
			list_to_do = list(set(todo[i]))
			if list_to_do != []:
				for j in xrange(len(list_to_do)):
					if times[list_to_do[j][0],list_to_do[j][1]] < t and tmp[list_to_do[j][0],list_to_do[j][1]]==0:
						tmp[list_to_do[j][0],list_to_do[j][1]] = shuffler[i]+1
						addon = expand(list_to_do[j][0],list_to_do[j][1],tmp2,dx,dy)
						if addon != []:
							for k in range(len(addon)):
								tmp_list[i].append(addon[k])
					elif times[list_to_do[j][0],list_to_do[j][1]] > t:
						tmp[list_to_do[j][0],list_to_do[j][1]] = 0
						tmp_list[i].append(list_to_do[j])
		#todo = np.copy(tmp_list)
		todo = tmp_list[:]
		#print tmp_list
		#print todo
		#exit()
		iterator += 1
		t+=dt
		print m,t,tmax
		if iterator%1000 == 0:
			np.savetxt('./'+filename+'_FMM_seg2.csv',tmp.astype(int), fmt='%i',delimiter=',')
			#exit()
	np.savetxt('./'+filename+'_FMM_seg2.csv',tmp.astype(int), fmt='%i',delimiter=',')

	# 		#exit()
	# 	iterator += 1
	# 	t+=dt
	# 	print t,tmax
	# np.savetxt('./segmented_slice_42.txt',tmp)


# def read_in_centroids(i):
# 	cx = []
# 	cy = []
# 	with open('../data/ch2_ims/centroids_updated_'+str(i)+'.txt') as f:
# 		for line in f:
# 			data = line.split()
# 			cy.append(int(data[0].split('{')[1].split(',')[0])-1)
# 			cx.append(int(data[1].split('}')[0])-1)
# 	return cx,cy

def read_in_centroids(filename):
	cx = []
	cy = []
	with open('./'+filename+'_cents2.txt') as f:
		for line in f:
			data = line.split(',')
			cx.append(int(float(data[0])))
			cy.append(int(float(data[1])))
	print 'Length of cx is: ', len(cx)
	#exit()
	return cx,cy
	
					
if __name__=='__main__':
	comm = MPI.COMM_WORLD
	size = comm.Get_size()
	rank = comm.Get_rank()	
	file_list = ["./b3.png","./b4.png","./b5.png"]
	#print file_list
	ll = len(file_list)
	print ll
	delta = ll/size
	start =  rank*delta
	stop = start +delta #+ 1
	if stop > ll:
		stop=ll
	local_list = file_list[start:stop]
	print local_list
	#
	for filetodo in local_list:
		print filetodo
		filename = filetodo.split('/')[1].split('.')[0]
		slice2 = read_in_frame(filetodo)
		#slice2 = scipy.ndimage.filters.gaussian_filter(slice2,2)
		a,b = np.shape(slice2)
		print np.amax(slice2)
		print np.amin(slice2)
		cx,cy = read_in_centroids(filename)
		plt.imshow(slice2,cmap='hot')
		plt.plot(cx,cy,'bo',markersize=3)
		plt.title('Raw Data and Seeds')
		plt.xlim([0,b])
		plt.ylim([0,a])
		plt.show()
		plt.savefig('./222.png', dpi=300,bbox_inches='tight')
		plt.clf()
		fmm = np.ones((a, b))
		for i in xrange(len(cx)):
			x1 = int(cx[i])
			y1 = int(cy[i])
			fmm[y1][x1] = -1
		print np.sum(fmm)
		#exit()
		#fmm=np.transpose(fmm)
		dist_mat = skfmm.distance(fmm)
		speed=np.genfromtxt('./'+filename+'_vel2.csv',delimiter=',')+0.0025
		#speed=scipy.ndimage.filters.gaussian_filter(speed,0.35)
		slice3 = read_in_frame(filetodo)
		print np.shape(slice3)
		dim1,dim2 = np.shape(slice3)
		# for m in xrange(dim1):
		# 	for n in xrange(dim2):
		# 		if slice3[m][n] == 0.0:
		# 			speed[m][n] = 1.0
		print np.amax(speed)
		print np.amin(speed)
		plt.imshow(speed,cmap='hot')
		plt.title('speed')
		plt.show()
		plt.savefig('./2222.png', dpi=300,bbox_inches='tight')
		plt.clf()
		t = skfmm.travel_time(fmm, speed)
		plt.imshow(t,cmap='hot')
		plt.show()
		plt.plot(cx,cy,'bo',markersize=3)
		plt.title('Travel Time and Seeds')
		plt.xlim([0,b])
		plt.ylim([0,a])
		plt.show()
		plt.savefig('./22222.png', dpi=300,bbox_inches='tight')
		plt.clf()
		print len(cx)
		print len(cy)
		#exit()

		segmentation3(filename,cx,cy,a,b,1,t,10)


