# this program computes the head for chunks an annotated SSF file / files
# the program requires a json file which identifies which are the possible heads
# Authors : Pruthwik Mishra, Juhi Tandon
# LTRC, IIIT-Hyderabad
import argparse
import re
import json
import ssfAPI
import os


def readJSONFile(jsonFilePath):
    """Read a json file."""
    dictChunkPOSMapping = json.load(open(jsonFilePath, 'r'))
    return dictChunkPOSMapping


def readFilesAndComputeHeadOfChunks(inputPath, chunkTagPOSMapping, outputPath):
    """Read files and compute head of chunks."""
    if not os.path.isdir(inputPath):
        d = ssfAPI.Document(inputPath)
        headComputedSentences = computeHeadOfChunks(d, chunkTagPOSMapping)
        writeListToFile(headComputedSentences, outputPath)
    else:
        fileList = ssfAPI.folderWalk(inputPath)
        newFileList = []
        for fileName in fileList:
            xFileName = fileName.split('/')[-1]
            if xFileName == 'err.txt' or xFileName.split('.')[-1] in ['comments', 'bak'] or xFileName[:4] == 'task':
                continue
            else:
                newFileList.append(fileName)
        for fl in newFileList:
            d = ssfAPI.Document(fl)
            headComputedSentences = computeHeadOfChunks(d, chunkTagPOSMapping)
            writeListToFile(headComputedSentences, os.path.join(outputPath, fl[fl.rfind('/') + 1:] + '.head'))


def computeHeadOfChunks(document, chunkTagPOSMapping):
    """Computer head of chunks."""
    headComputedSentences = []
    for tree in document.nodeList:
        headFound = True
        for indexChunk, chunkNode in enumerate(tree.nodeList):
            if re.search('^NULL.+', chunkNode.type):
                for node in chunkNode.nodeList:
                    if node.getAttribute('af'):
                        chunkNode.addAttribute('af', node.getAttribute('af'))
                    else:
                        chunkNode.addAttribute('af', 'null,unk,,,,,,')
                    chunkNode.addAttribute('head', node.name)
            else:
                probablePOSTagsList = [chunkTagPOSMapping[
                    key] for key in chunkTagPOSMapping if re.search(key, chunkNode.type)]
                if len(probablePOSTagsList) > 0:
                    probablePOSTags = probablePOSTagsList[0]
                    matchedPOSTags = []
                    for node in chunkNode.nodeList:
                        if re.search(probablePOSTags, node.type) and not re.search('^NULL', node.lex):
                            matchedPOSTags.append(
                                (node.name, node.type, node.getAttribute('af')))
                    if len(matchedPOSTags) > 0:
                        chunkNode.addAttribute('af', matchedPOSTags[-1][2])
                        chunkNode.addAttribute('head', matchedPOSTags[-1][0])
                    else:
                        if chunkNode.type == 'NP':
                            matchedPOSTags = []
                            for node in chunkNode.nodeList:
                                if re.search('QT_QT.+|N_NST|QT__QT.+|N__NST', node.type):
                                    matchedPOSTags.append(
                                        (node.name, node.type, node.getAttribute('af')))
                            if len(matchedPOSTags) > 0:
                                chunkNode.addAttribute('af', matchedPOSTags[-1][2])
                                chunkNode.addAttribute('head', matchedPOSTags[-1][0])
            if not chunkNode.getAttribute('head'):
                headFound = headFound and False
            else:
                headFound = headFound and True
        if headFound:
            headComputedSentences.append(tree.printSSFValue(False))
        else:
            continue
    return headComputedSentences


def writeListToFile(dataList, filePath):
    """Write a list to a file."""
    with open(filePath, 'w', encoding='utf-8') as fileWrite:
        fileWrite.write('\n'.join(dataList) + '\n')


def main():
    """Pass arguments and call functions here."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='inp', help='Enter the input file or folder path')
    parser.add_argument('--output', dest='out', help='Enter the output file or folder path')
    parser.add_argument('--json', dest='json', help='Enter the JSON file path containing ChunkTagToPOSMapping')
    args = parser.parse_args()
    if os.path.isdir(args.inp) and not os.path.isdir(args.out):
        os.mkdir(args.out)
    chunkTagPOSMapping = readJSONFile(args.json)
    readFilesAndComputeHeadOfChunks(args.inp, chunkTagPOSMapping, args.out)


if __name__ == '__main__':
    main()
