from __future__ import division
import argparse
import numpy as np
from itertools import izip

from nested_sampling import compute_heat_capacity

def get_energies(fnames, block=False):
    """read energies from a list of file names and return as one list
    """
    if len(fnames) == 1:
        return np.genfromtxt(fnames[0])
    else:
        eall = []
        for fname in fnames:
            e = np.genfromtxt(fname)
            eall += e.tolist()
        eall.sort(key=lambda x: -x)
        return np.array(eall).flatten()

def main():   
    parser = argparse.ArgumentParser(description="load energy intervals and compute cv", 
                                     epilog="if more than one file name is given the energies from all runs will be combined and sorted."
                                     "  the number of replicas will be the sum of the replicas used from all runs (automated!!!)")
    parser.add_argument("K", type=int, help="number of replicas")
    parser.add_argument("fname", nargs="+", type=str, help="filenames with energies")
    parser.add_argument("-P", type=int, help="number of cores for parallel run", default=1)
    parser.add_argument("--Tmin", type=float,help="set minimum temperature for Cv evaluation (default=0.01)",default=0.01)
    parser.add_argument("--Tmax", type=float,help="set maximum temperature for Cv evaluation (default=0.5)",default=0.5)
    parser.add_argument("--nT", type=int,help="set number of temperature in the interval Tmin-Tmax at which Cv is evaluated (default=500)",default=500)
    parser.add_argument("--ndof", type=int, help="number of degrees of freedom (default=0)", default=0)
    parser.add_argument("--live", action="store_true", help="use live replica energies (default=False), numerically unstable for K>2.5k.",default=False)
    parser.add_argument("--live-not-stored", action="store_true", help="turn this flag on if you're using a set of data that does not contain the live replica.",default=False)
    parser.add_argument("-o", type=str, default="cv", help="change the prefix of the output files")
    args = parser.parse_args()
    print args.fname
    print args


    energies = get_energies(args.fname)
    print "energies size", np.size(energies)
    
    print "parallel nprocessors", args.P
    print "replicas", args.K
    
    #in the improved parallelization we save the energies of the replicas at the live replica but the ln(dos) underflows for these, hence this:
    if not args.live_not_stored:
        energies = energies[:-args.K]
    else:
        assert not args.live, "cannot use live replica under any circumstances if they have not been saved" 
    
    #make nd-arrays C contiguous # js850> this will already be the case 
#    energies = np.array(energies, order='C')
    
    # do the computation
    T, Cv, U, U2 = compute_heat_capacity(energies, args.K, npar=args.P, 
                                         ndof=args.ndof, Tmin=args.Tmin, Tmax=args.Tmax, 
                                         nT=args.nT, live_replicas=args.live)
    
    # print to cv.dat 
    with open(args.o+".dat", "w") as fout:
        fout.write("#T Cv <E> <E^2>\n")
        for vals in izip(T, Cv, U, U2):
            fout.write("%.16g %.16g %.16g %.16g\n" % vals)
    
    # make a plot and save it
    import matplotlib
    matplotlib.use('PDF')
    import pylab as pl
    pl.plot(T, Cv)
    pl.xlabel("T")
    pl.ylabel("Cv")
    pl.savefig(args.o+".pdf")
        
    
if __name__ == "__main__":
    main()
