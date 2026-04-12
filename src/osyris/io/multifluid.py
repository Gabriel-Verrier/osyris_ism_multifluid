# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Osyris contributors (https://github.com/osyris-project/osyris)
import numpy as np
import os
from .reader import Reader, ReaderKind
from . import utils


class MfReader(Reader):

    def __init__(self):
        super().__init__(kind=ReaderKind.AMR)

    def initialize(self, meta, units, select, ramses_ism):
        self.initialized = False
        if select is False:
            return

        # Read the number of variables from the hydro_file_descriptor.txt
        # and select the ones to be read if specified by user
        fname = os.path.join(meta["infile"], "mf_file_descriptor.txt")
        try:
            if ramses_ism:
                desc_from_file = []
                with open(fname, "r") as f:
                    data = f.readlines()
                nvar = int(data[0].split()[-1])
                #print("nvar=",nvar) #commented
                #print("data=",data)
                for i in range(nvar):
                    comp = [i + 1, data[i + 1].split()[-1], "d"]
                    desc_from_file.append(comp)
                desc_from_file = np.array(desc_from_file)
            else:
                desc_from_file = np.loadtxt(fname, dtype=str, delimiter=",")
        except IOError:
            return

        descriptor = {
            desc_from_file[i, 1].strip(): desc_from_file[i, 2].strip()
            for i in range(len(desc_from_file))
        }

        self.descriptor_to_variables(descriptor=descriptor,
                                     meta=meta,
                                     units=units,
                                     select=select)
        #list_file= os.listdir(meta["infile"])
        #ff= os.path.join(meta["infile"], "info_mf_")
        #for file in list_file:
        #    if(file.startswith(ff)):
        #        fname=file
        #meta_mf = utils.read_parameter_file(fname=fname)
        #for key in meta_mf:
        #    self.meta[key]=meta_mf[key]
        self.initialized = True

    def read_header(self, info):

        new_osyris=True 
        # Here new_osyris is a keyword which is the momento of various changes 
        # in the way additional multifluid information is output (see the RAMSES code (ramses/multifluid/output_multifluid.f90), multifluid file descriptor and info_mf).
        # Multifluid outputs and info file was originally the same as for hydro, which is read with the new_osyris=False option.
        # In particular, the structure of the file given in the subroutine backup_mf was
        """
        fileloc=TRIM(filename)//TRIM(nchar)
        open(unit=ilun,file=fileloc,form='unformatted')
        write(ilun)ncpu
        write(ilun)nvarflu
        write(ilun)ndim
        write(ilun)nlevelmax
        write(ilun)nboundary
        write(ilun)gamma
        """
        # It has originally been used for the development of the multifluid (2023-2024).
        # When the first multifluid simulations with a MRN distribution started,
        # we provided in the outputs the grain sizes (to check the initialisation, the restart, to avoid ambiguities in the post-processing).
        # Our first approach was to remove write(ilun)gamma from the format (because it is not a multifluid parameter) and to add write(ilun)mf_grainsize instead.
        # The resulting modification of osyris (multifluid read_header) is maintained through new_osyris=True.
        # It allows to read several multifluid simulations run in 2025.
        # For a more versatile post-processing, we went back to the original format
        # and we output the grain sizes in the info_mf text files instead.
        # Therefore, new_osyris=False is the updated version, in agreement with the current RAMSES code.
        # Note that grain intrinsic densities can be also be read now thanks to new_osyris=False.


        self.offsets["i"] += 5 #due to above lines
        self.offsets["n"] += 5
        #print(info)
        list_file= os.listdir(info["infile"])
        #print(list_file)
        ff="info_mf_"
        for file in list_file:
            #print(file)
            if(file.startswith(ff)):
                filename=file
        meta_mf = utils.read_parameter_file(info["infile"]+'/'+filename)
        for key in meta_mf:
            self.meta[key]=meta_mf[key]
            info[key]=meta_mf[key]
        
        # Detection of the multifluid output format (version)
        if('mf_grain_size_1' in self.meta):
            new_osyris=False
        
        if(new_osyris==False):

            #Gather in arrays some keys (grain sizes and grain densities)
            mf_grainsize=np.array([])
            for ifluid in range(1,info['nfluid']+1):
                mf_grainsize=np.append(mf_grainsize,info['mf_grain_size_'+str(ifluid)])
            info["mf_grainsize"] = mf_grainsize

            if('mf_grain_density_1' in self.meta):
                mf_grain_density=np.array([])
                for ifluid in range(1,info['nfluid']+1):
                    mf_grain_density=np.append(mf_grain_density,info['mf_grain_density_'+str(ifluid)])
                info["mf_graindens"] = mf_grain_density

            #Note: The info['mf_grain_size_'+str(ifluid)] and info['mf_grain_density_'+str(ifluid)] could be removed from the dictonnary keys.

        if new_osyris :
            # nfluid
            [self.meta["nfluid"]] = utils.read_binary_data(fmt="i",
                                                            content=self.bytes,
                                                            offsets=self.offsets)
            info["nfluid"]=self.meta["nfluid"]
            # grainsizes
            self.offsets["i"] += 0 
            self.offsets["n"] += 0 

            info["mf_grainsize"] = np.array( utils.read_binary_data(fmt="{}d".format(self.meta["nfluid"]),content=self.bytes, offsets=self.offsets) ) 
        else:
            #self.offsets["d"] += 1
            [info["gamma_mf"]] = utils.read_binary_data(fmt="d",
                                                 content=self.bytes,
                                                 offsets=self.offsets)
            #[info["gamma"]] = utils.read_binary_data(fmt="d",content=self.bytes, offsets=self.offsets) #hydro gamma

    def read_domain_header(self):
        self.offsets['n'] += 2
        self.offsets['i'] += 2
