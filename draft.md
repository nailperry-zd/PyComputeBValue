# Example
python ComputeBValue.py -b 2000 -o C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b2000t_synthesised.nii.gz mono C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b50t.nii.gz:50  C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b400t.nii.gz:400 C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b800t.nii.gz:800 C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b1200t.nii.gz:1200

# ComputeUnknownBValueFileNames
1. Sort all the files in one DICOM folder according to the z position of each slice.
2. Identify contiguous range of slices with the same z position. 
   - For each z position, we should get numBValues slices. If we have b50,400,800,1200, then numBValues should be 4.
3. Sort the slices (with the same z position) by intensity.
   - For a specific z position, we can get numBValues slices. We can differentiate them by intensity.