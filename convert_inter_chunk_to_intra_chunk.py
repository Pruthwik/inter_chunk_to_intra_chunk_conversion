"""Convert interchunk to intrachunk."""
from argparse import ArgumentParser
import os
from pickle import load
from collections import OrderedDict
from re import search


def load_object_from_pickle(pickle_file):
	"""Load an object from the pickle file."""
	with open(pickle_file, 'rb') as pickle_load:
		return load(pickle_load)


def read_lines_from_file(file_path):
	"""Read lines from a file using its file path."""
	with open(file_path, 'r', encoding='utf-8') as file_read:
		return file_read.readlines()


def write_lines_to_file(lines, file_path):
	"""Write lines to a file."""
	with open(file_path, 'w', encoding='utf-8') as file_write:
		file_write.write('\n'.join(lines))


def create_key_val_pairs_from_morph(morph):
	"""Create key and value pairs from morph text."""
	dict_attrib = OrderedDict()
	for key_val in morph.split():
		key, val = key_val.split('=')
		val = val[1: -1]
		dict_attrib[key] = val
	return dict_attrib


def find_intra_chunk_deprel_using_pos(parent_pos, child_pos):
	"""Find intra chunk deprel using POS."""
	if child_pos in ['PSP', 'N_NST'] and search('N\_*|PR\_*|V\_*', parent_pos):
		dep_rel = 'lwg__psp'
	elif child_pos == 'V_VAUX' and search('V\_*', parent_pos):
		dep_rel = 'lwg__vaux'
	elif child_pos in ['N_NN', 'N_NNP'] and parent_pos in ['N_NN', 'N_NNP']:
		dep_rel = 'pof__cn'
	elif child_pos == 'RP_RPD' and parent_pos != 'RP\_RPD':
		dep_rel = 'lwg__rp'
	elif child_pos == 'RP_NEG':
		dep_rel = 'lwg__neg'
	elif child_pos in ['RD_SYM', 'RD_PUNC']:
		dep_rel = 'rsym'
	elif search('QT\_*', child_pos):
		dep_rel = 'nmod__adj'
	elif search('N\_NN|N\_NNP', child_pos) and search('N\_NN|N\_NNP', parent_pos):
		dep_rel = 'pof__cn'
	elif child_pos == 'RP_INTF' and parent_pos in ['JJ', 'RB']:
		dep_rel = 'jjmod__intf'
	elif child_pos == 'RP_NEG':
		dep_rel = 'lwg__neg'
	elif child_pos == 'RP_INJ' and parent_pos != 'RP_INJ':
		dep_rel = 'lwg__uh'
	elif search('DM\_*', child_pos) and search('PR\_*|N\_*', parent_pos):
		dep_rel = 'nmod__adj'
	elif child_pos == 'JJ' and search('PR\_*|N\_*', parent_pos):
		dep_rel = 'nmod__adj'
	elif child_pos == 'RB' and search('V\_*', parent_pos):
		dep_rel = "vmod__adv"
	elif child_pos == 'PR_PRQ' and search('N\_*', parent_pos):
		dep_rel = 'mod__wq'
	else:
		dep_rel = 'mod'
	return dep_rel


def remove_continous_blank_lines(lines):
	"""Remove continuous blank lines"""
	updated_lines = []
	for index, line in enumerate(lines):
		if index in [0, len(lines) - 1] and not line.strip():
			continue
		elif not line.strip() and not updated_lines[-1].strip():
			continue
		else:
			updated_lines.append(line)
	return updated_lines


def convert_attribute_dict_into_morph_string(dict_attrib):
	"""Convert attribute dictionary into morph string."""
	morph_keys_and_values = [key + "='" + val + "'" for key, val in dict_attrib.items()]
	return "<fs " + ' '.join(morph_keys_and_values) + ">"


def convert_into_inter_chunk_for_file(lines):
	"""Convert into interchunk format for lines in a file."""
	updated_lines = []
	sentence_dict = OrderedDict()
	chunk_head_to_id = OrderedDict()
	chunk_id_to_head = OrderedDict()
	chunk_head_pos = {}
	chunk_drels = {}
	prob_sent = False
	for line in lines:
		line = line.strip()
		if line:
			if "<Sentence" in line:
				updated_lines.append(line)
			elif "</Sentence>" in line:
				if prob_sent:
					prob_sent = False
					updated_lines.pop()
					continue
				token_cntr = 1
				try:
					for chunk in sentence_dict:
						parent_pos = chunk_head_pos[chunk]
						chunk_tokens_info = sentence_dict[chunk]
						head_token_name = chunk_id_to_head[chunk]
						prev_drel = ''
						for chunk_token_info in chunk_tokens_info:
							morph_dict = chunk_token_info[2]
							if chunk_token_info[4] == 'child':
								child_pos = chunk_token_info[1]
								drel = find_intra_chunk_deprel_using_pos(parent_pos, child_pos)
								child_token = chunk_token_info[0]
								if drel == 'mod':
									if search('^' + child_token + '\d+$', head_token_name):
										drel = 'pof__redup'
								if 'vaux' in drel and 'vaux' in prev_drel:
									drel = drel + '_cont'
								elif 'psp' in drel and 'psp' in prev_drel:
									drel = drel + '_cont'
								morph_dict['drel'] = drel + ':' + head_token_name
								morph_dict['chunkType'] = 'child:' + chunk
								prev_drel = drel
							else:
								if chunk in chunk_drels:
									drel_head, parent_head_chunk = chunk_drels[chunk].split(':')
									morph_dict['drel'] = drel_head + ':' + chunk_id_to_head[parent_head_chunk]
								morph_dict['chunkType'] = 'head:' + chunk
								morph_dict['chunkId'] = chunk
							morph_string = convert_attribute_dict_into_morph_string(morph_dict)
							updated_line = '\t'.join([str(token_cntr), chunk_token_info[0], chunk_token_info[1], morph_string])
							updated_lines.append(updated_line)
							token_cntr += 1
					updated_lines.append(line)
					sentence_dict = OrderedDict()
					chunk_head_to_id = OrderedDict()
					chunk_id_to_head = OrderedDict()
					chunk_head_pos = {}
					chunk_drels = {}
				except Exception:
					for i in range(len(updated_lines) - 1, -1, -1):
						if search('^<Sentence id=', updated_lines[i]):
							break
					for j in range(len(updated_lines) - i):
						updated_lines.pop()
					sentence_dict = OrderedDict()
					chunk_head_to_id = OrderedDict()
					chunk_id_to_head = OrderedDict()
					chunk_head_pos = {}
					chunk_drels = {}
			elif search('^\d+\t\(\(\t', line):
				addr, header, chunk_tag, chunk_morph = line.split('\t')
				chunk_attrib_dict = create_key_val_pairs_from_morph(chunk_morph[4: -1])
				if 'comment' in chunk_attrib_dict:
					if 'probsent' in chunk_attrib_dict['comment']:
						prob_sent = True
				if prob_sent:
					continue
				chunk_head = chunk_attrib_dict['head']
				chunk_id = chunk_attrib_dict['name']
				chunk_head_to_id[chunk_head] = chunk_id
				chunk_id_to_head[chunk_id] = chunk_head
				if 'drel' in chunk_attrib_dict:
					chunk_drels[chunk_id] = chunk_attrib_dict['drel']
			elif line == '))':
				continue
			else:
				if prob_sent:
					continue
				addr, token, pos, morph = line.split('\t')
				token_attrib_dict = create_key_val_pairs_from_morph(morph[4: -1])
				token_name = token_attrib_dict['name']
				if token_name in chunk_head_to_id:
					chunk_type = 'head'
					chunk_head_pos[chunk_id] = pos
				else:
					chunk_type = 'child'
				sentence_dict.setdefault(chunk_id, []).append((token, pos, token_attrib_dict, token_name, chunk_type))
		else:
			updated_lines.append(line)
	return updated_lines


def main():
	"""Pass arguments and call functions here."""
	parser = ArgumentParser()
	parser.add_argument('--input', dest='inp', help='Enter the input file path')
	parser.add_argument('--output', dest='out', help='Enter the output file path')
	args = parser.parse_args()
	if not os.path.isdir(args.inp):
		lines = read_lines_from_file(args.inp)
		updated_lines = convert_into_inter_chunk_for_file(lines)
		updated_lines = remove_continous_blank_lines(updated_lines)
		write_lines_to_file(updated_lines, args.out)
	else:
		if not os.path.isdir(args.out):
			os.makedirs(args.out)
		for root, dirs, files in os.walk(args.inp):
			for fl in files:
				print(fl)
				file_path = os.path.join(root, fl)
				lines = read_lines_from_file(file_path)
				updated_lines = convert_into_inter_chunk_for_file(lines)
				updated_lines = remove_continous_blank_lines(updated_lines)
				if '.new.head' in fl:
					file_name = fl.replace('.new.head', '')
				elif '.head' in fl:
					file_name = fl.replace('.head', '')
				else:
					file_name = fl
				output_path = os.path.join(args.out, file_name)
				write_lines_to_file(updated_lines, output_path)


if __name__ == '__main__':
	main()