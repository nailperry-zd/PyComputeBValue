# 
# Nathan Lay
# AI Resource at National Cancer Institute
# National Institutes of Health
# September 2021
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR(S) ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR(S) BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 

import sys
import os
import argparse
from common import LoadBValueImages, ResolveBValueImages, LoadDicomImage, LoadImage
from models import MonoExponentialModel
import re

modelTable = {
  "mono": MonoExponentialModel
}

def main(modelType, outputPath, imagePaths, targetBValue, scale=1.0, seriesNumber=13701, saveADC=False, saveKurtosis=False, savePerfusion=False, compress=False, adcPath=None, initialBValue=0.0):
    if modelType not in modelTable:
        print(f"Error: Unknown model type '{modelType}'.", file=sys.stderr)
        exit(1)

    model = modelTable[modelType]()

    adcImage = None

    if adcPath is not None:
        if os.path.isdir(adcPath):
            adcImage = LoadDicomImage(adcPath)
        else:
            adcImage = LoadImage(adcPath)

        if adcImage is None:
            print(f"Error: Could not load ADC image '{adcPath}'.", file=sys.stderr)
            exit(1)

        print("Info: Loaded ADC image.")

        if not model.SetADCImage(adcImage):
            print(f"Warning: '{modelType}' model does not support using existing ADC image.", file=sys.stderr)

    images = []

    for imagePath in imagePaths:
        tmpImages = LoadBValueImages(imagePath)

        if tmpImages is None:
            print(f"Error: Could not load b-value image from '{imagePath}'.", file=sys.stderr)
            exit(1)

        images += tmpImages

    imagesByBValue = ResolveBValueImages(images, adcImage, initialBValue=initialBValue)

    if imagesByBValue is None:
        print(f"Error: Could not resolve b-values.", file=sys.stderr)
        exit(1)

    loadedBValues = list(imagesByBValue.keys())
    loadedBValues.sort()

    for bValue in loadedBValues:
        print(f"Info: Loaded b = {bValue}")

    model.SetTargetBValue(targetBValue)
    model.SetImages(imagesByBValue)
    model.SetOutputPath(outputPath)
    model.SetSeriesNumber(seriesNumber)
    model.SetCompress(compress)
    model.SetBValueScale(scale)

    if saveADC and not model.SaveADC():
        print(f"Warning: '{modelType}' model does not support saving ADC images.", file=sys.stderr)

    if savePerfusion and not model.SavePerfusion():
        print(f"Warning: '{modelType}' model does not support saving perfusion fraction images.", file=sys.stderr)

    if saveKurtosis and not model.SaveKurtosis():
        print(f"Warning: '{modelType}' model does not support saving kurtosis images.", file=sys.stderr)

    print(f"Info: Calculating b-{targetBValue}")

    if not model.Run():
        print("Error: Failed to compute b-value image.", file=sys.stderr)
        exit(1)

    if not model.SaveImages():
        print("Error: Failed to save output images.", file=sys.stderr)
        exit(1)

def tst_commandline():
    parser = argparse.ArgumentParser(description="PyComputeBValue")
    parser.add_argument("-a", "--save-adc", dest="saveADC", action="store_true", default=False, help="Save calculated ADC. The output path will have _ADC appended (folder --> folder_ADC or file.ext --> file_ADC.ext).")
    parser.add_argument("-b", "--target-b-value", dest="targetBValue", required=True, type=float, help="Target b-value to calculate.")
    parser.add_argument("-c", "--compress", dest="compress", action="store_true", default=False, help="Compress output.")
    parser.add_argument("-k", "--save-kurtosis", dest="saveKurtosis", action="store_true", default=False, help="Save calculated kurtosis image. The output path will have _Kurtosis appended.")
    parser.add_argument("-n", "--series-number", dest="seriesNumber", type=int, default=13701, help="Series number for calculated b-value image.")
    parser.add_argument("-o", "--output-path", dest="outputPath", required=True, type=str, help="Output path which may be a folder for DICOM output or a medical image format file.")
    parser.add_argument("-p", "--save-perfusion", dest="savePerfusion", action="store_true", default=False, help="Save calculated perfusion fraction image. The output path will have _Perfusion appended.")
    parser.add_argument("-s", "--scale", dest="scale", type=float, default=1.0, help="Scale factor of target b-value image intensities.")
    parser.add_argument("-A", "--adc-path", dest="adcPath", required=False, type=str, default=None, help="Load an existing ADC image to use for computing a b-value image.")
    parser.add_argument("-I", "--initial-b-value", dest="initialBValue", required=False, type=float, default=0.0, help="Initial expected b-value in a diffusion series of unknown b-values.")
    parser.add_argument("modelType", type=str, choices=list(modelTable.keys()), help="Diffusion model to use.")
    parser.add_argument("imagePaths", type=str, nargs='+', help="B-value diffusion series folders and image paths. Image paths may optionally be suffixed with ':bvalue' to indicate the diffusion b-value of the image. DICOM paths suffixed with ':-1' indicate that DICOM should be ignored when querying the b-value of the image.")

    args = parser.parse_args()

    main(**vars(args))

def tst_single_input():
    modelType = 'mono'
    # test input:NIFTI
    # inputType = 'nifti'
    # imagePaths = [r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b50t.nii.gz:50',r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b400t.nii.gz:400', r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b800t.nii.gz:800', r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b1200t.nii.gz:1200']
    # test input:individual DICOM
    # inputType = 'individual_dicom'
    # imagePaths = [r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b50t:50',r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b400t:400', r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b800t:800', r'C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist038\DWI\ep_b1200t:1200']
    # test input:whole DICOM
    inputType = 'whole_dicom'
    imagePaths = [r"C:\Users\dzha937\DEV\Data_Vault\MRHIST\Patient Registration Results\mrhist039\data\in_vivo_mri\dwi:50,400,800,1200"]
    targetBValue = 2000
    outputPath = rf"C:\hpc\dzha937\Ella\Data\MRHIST\Originals\mrhist039\DWI\ep_b{targetBValue}t_synthesised_{inputType}.nii.gz"
    main(modelType, outputPath, imagePaths, targetBValue)



def extract_number(string):
    """
    给定一个包含数字的字符串,提取其中的数字部分并返回。
    """
    # 使用正则表达式提取数字部分
    import re
    number = re.findall(r'\d+', string)

    # 如果找到了数字,返回第一个数字
    if number:
        return int(number[0])
    else:
        return None

def get_all_subdirs(filepath):
    """
    给定一个文件路径,收集所有的子目录路径并返回一个列表。
    """
    subdirs = []
    for root, dirs, files in os.walk(filepath):
        for dir in dirs:
            # subdirs.append(os.path.join(root, dir))
            b_value = extract_number(dir)
            subdirs.append(f'{os.path.join(root, dir)}:{b_value}')
    return subdirs
def find_subdir(directory, pattern):
    for dirpath, dirnames, filenames in os.walk(directory):
        for dirname in dirnames:
            if re.match(pattern, dirname):
                return os.path.join(dirpath, dirname)
    return f'7_{pattern}'
def synthesise_b2000(patien_range, dwi_dicom_filename_pattern, b_value_hint):# avoid using 'test_' because it may trigger pytest
    for i in patien_range:
        pid = str(i).zfill(3)
        bvalue_output_dir = rf'C:\Users\dzha937\DEV\Data_Processed\MRHIST\mrhist{pid}'
        if not os.path.exists(bvalue_output_dir):
            os.makedirs(bvalue_output_dir)
        modelType = 'mono'
        source_dwi_dir = rf"C:\Users\dzha937\DEV\Data_Vault\MRHIST\Patient Images\mrhist{pid}\in_vivo_mri"
        imagePaths = [fr"{find_subdir(source_dwi_dir, dwi_dicom_filename_pattern)}:{b_value_hint}"]
        targetBValue = 2000
        outputPath = os.path.join(bvalue_output_dir, rf"in_b{targetBValue}.nii.gz")
        main(modelType, outputPath, imagePaths, targetBValue)

def synthesise_b2000_039_to_070():# avoid using 'test_' because it may trigger pytest
    for i in range(39, 71):
        if i == 67:
            continue
        pid = str(i).zfill(3)
        bvalue_output_dir = rf'C:\Users\dzha937\DEV\Data_Processed\MRHIST\mrhist{pid}'
        if not os.path.exists(bvalue_output_dir):
            os.makedirs(bvalue_output_dir)
        modelType = 'mono'
        imagePaths = [fr"C:\Users\dzha937\DEV\Data_Vault\MRHIST\Patient Registration Results\mrhist{pid}\data\in_vivo_mri\dwi:50,400,800,1200"]
        targetBValue = 2000
        outputPath = os.path.join(bvalue_output_dir, rf"in_b{targetBValue}.nii.gz")
        main(modelType, outputPath, imagePaths, targetBValue)

if __name__ == '__main__':
    # tst_multiple_inputs()
    # tst_single_input()
    # synthesise_b2000_039_to_070()
    pattern_005_to_008 = r'\d+_ep2d_tra_b50_b400_b800_p2_192$'
    range_005_to_008 = range(5, 9)
    b_value_hint_005_to_008 = '50,400,800'

    pattern_009_to_038 = r'\d+_ep2d_tra_b50_b400_b800_b1200$'
    range_009_to_038 = range(9, 39)
    b_value_hint_009_to_038 = '50,400,800,1200'
    synthesise_b2000(range_005_to_008, pattern_005_to_008, b_value_hint_005_to_008)
    # synthesise_b2000(range_009_to_038, pattern_009_to_038, b_value_hint_009_to_038)
