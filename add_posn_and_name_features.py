"""Add posn and name features to token fs features."""
from argparse import ArgumentParser
import re
import os
from collections import OrderedDict


def find_ssf_sentences(text):
	"""Find sentences in SSF format in text."""
	return re.findall('(<Sentence id=.*?>)\n(.*?)\n(</Sentence>)', text, re.S)


def read_text_from_file(file_path):
	"""Read text from a file."""
	with open(file_path, 'r', encoding='utf-8') as file_read:
		return file_read.read().strip()


def convert_attribute_dict_into_morph_string(dict_attrib):
	"""Convert attribute dictionary into morph string."""
	morph_keys_and_values = [key + "='" + val + "'" for key, val in dict_attrib.items()]
	return "<fs " + ' '.join(morph_keys_and_values) + ">"


def create_key_val_pairs_from_morph(morph):
	"""Create key and value pairs from morph text."""
	dict_attrib = OrderedDict()
	for key_val in morph.split():
		key, val = key_val.split('=', 1)
		val = val[1: -1]
		dict_attrib[key] = val
	return dict_attrib


def write_lines_to_file(lines, file_path):
	"""Write lines to a file."""
	with open(file_path, 'w', encoding='utf-8') as file_write:
		file_write.write('\n'.join(lines))


def add_posn_name_features_in_sentences(ssf_sentences):
	"""Add posn and name features in SSF sentences."""
	updated_lines = []
	for header, sentence_text, footer in ssf_sentences:
		posn = 0
		updated_sentence = []
		tokens = []
		chunks = []
		posn_cntr = 10
		updated_lines.append(header)
		for line in sentence_text.split('\n'):
			if line == '\t))':
				updated_lines.append(line)
			elif '\t((\t' in line:
				addr, braces, chunk_tag, morph = line.split('\t')
				morph_dict = create_key_val_pairs_from_morph(morph[4: -1])
				if 'name' in morph_dict:
					del morph_dict['name']
				if chunk_tag not in chunks:
					morph_dict['name'] = chunk_tag
					chunks.append(chunk_tag)
				else:
					count_chunk_tag = chunks.count(chunk_tag)
					morph_dict['name'] = chunk_tag + str(count_chunk_tag + 1)
					chunks.append(chunk_tag)
				morph_string = convert_attribute_dict_into_morph_string(morph_dict)
				updated_lines.append('\t'.join([addr, braces, chunk_tag, morph_string]))
			elif re.search('^\d+\.\d+\t', line):
				addr, token, pos_tag, morph = line.split('\t')
				pos_tag = pos_tag.replace('__', '_')
				morph_dict = create_key_val_pairs_from_morph(morph[4: -1])
				if 'name' in morph_dict:
					del morph_dict['name']
				if 'posn' in morph_dict:
					del morph_dict['posn']
				if token not in tokens:
					morph_dict['name'] = token
					tokens.append(token)
				else:
					count_token = tokens.count(token)
					morph_dict['name'] = token + str(count_token + 1)
					tokens.append(token)
				morph_dict['posn'] = str(posn_cntr)
				posn_cntr += 10
				morph_string = convert_attribute_dict_into_morph_string(morph_dict)
				updated_lines.append('\t'.join([addr, token, pos_tag, morph_string]))
		updated_lines.append(footer)
		updated_lines.append('')
	return updated_lines


def main():
	"""Pass arguments and call functions here."""
	parser = ArgumentParser()
	parser.add_argument('--input', dest='inp', help="give the input file or folder path")
	parser.add_argument('--output', dest='out', help="give the output file or folder path")
	args = parser.parse_args()
	if not os.path.isdir(args.inp):
		text = read_text_from_file(args.inp)
		ssf_sentence_info = find_ssf_sentences(text)
		updated_lines = add_posn_name_features_in_sentences(ssf_sentence_info)
		write_lines_to_file(updated_lines, args.out)
	else:
		if not os.path.isdir(args.out):
			os.makedirs(args.out)
		for root, dirs, files in os.walk(args.inp):
			for fl in files:
				print(fl)
				file_path = os.path.join(root, fl)
				text = read_text_from_file(file_path)
				ssf_sentence_info = find_ssf_sentences(text)
				updated_lines = add_posn_name_features_in_sentences(ssf_sentence_info)
				output_path = os.path.join(args.out, fl)
				write_lines_to_file(updated_lines, output_path)


if __name__ == '__main__':
	main()
