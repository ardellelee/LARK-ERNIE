'''
Created: July 30, 2019

Description:
Post-process the NER results of ERNIE. Produce datasets for ERNIE RE.

Steps:
1. Extract entities from the row-wise NER result file
2. Add ['entity_list'] filed for each document in json file
    entity_dict(text= ,
                type= ,
                # role= )
3. Apply RelationTransformer to generate data for RE prediction


Format:
    Char	Actual	Pred
    #doc-0
    查	B-人物	B-人物
    尔	I-人物	I-人物
    斯	I-人物	I-人物

Desired Output:
A .tsv file with two columns: docid, text_a.
    'text_a' should be masks subj and obj

'''
import csv
from collections import namedtuple
from pprint import pprint
from itertools import permutations
from argparse import ArgumentParser, FileType



class NEROutputTransformer(object):

    def read_file(self, fpath):
        f = open(fpath, 'r').readlines()
        headers = f[0].rstrip().split('\t')
        lines = [line.rstrip() for line in f[1:]]
        Example = namedtuple('Example', headers)

        doc_starts = [i for i, line in enumerate(lines) if line.startswith("#dev-")] + [len(lines)]         # add end
        # print(len(doc_starts))

        docs = []
        for i in range(len(doc_starts) - 1):
            _start = doc_starts[i]
            _end = doc_starts[i + 1]
            docid = lines[_start].strip("#")
            doc_lines = [line.split('\t') for line in lines[_start + 1:_end] if line not in ['\n', '']]         # remove blank rows
            doc_lines = [Example(*line) for line in doc_lines]

            docs.append(dict(docid=docid,
                             lines=doc_lines))
        return docs


    def transform(self, docs):
        '''
        Input format:
            {'docid': 'dev-0',
            'lines': [Example(Char='查', Actual='B-人物', Pred='B-人物'),
                    Example(Char='尔', Actual='I-人物', Pred='I-人物'),
                    Example(Char='斯', Actual='I-人物', Pred='I-人物')]
            }
        Output format:
            {'docid': 'dev-0',
            'text': str, entities masked
            }
        '''
        relation_mask = '[MASK]'
        transformed = []
        for d in docs:
            docid = d.get('docid', '')
            lines = d.get('lines', [])

            token_seq = [line.Char for line in lines]
            pred_labels = [line.Pred for line in lines]
            system_entities = self._extract_entities(token_seq, pred_labels)

            '''Pair-wise Entity Masking
            
            Note: system entities may occur multiple times in text, Example:
            "李 治 即 位 后 ， 萧 淑 妃 受 宠 ， 王 皇 后 为 了 排 挤 萧 淑 妃 ， 答 应 李 治 让 身 在 感 业 寺 的 武 则 天 续 起 头 发 ， 重 新 纳 入 后 宫"
            
            "李 治" and "萧 淑 妃" both have 2 occurrences, but we should only mask one.
            
            So masking shall be located:
             1) by token index, or
             2) by matching the string, but only replace the first occurrence
            
            '''
            relation_instances = []
            for subj, obj in permutations(system_entities, 2):  # n entities -> n*(n-1) pairs
                text = ' '.join(token_seq)
                text = text.replace(subj['text'], "%s%s" % (relation_mask, relation_mask), 1)
                text = text.replace(obj['text'], relation_mask, 1)

                relation_instances.append(dict(text_a=text, docid=docid))
            # end for

            transformed += relation_instances

        return transformed


    def _extract_entities(self, words, labels):
        '''
        Given a sequence of words (tokens) and a sequence of labels,
        return a list of extracted entities
        '''
        assert len(words) == len(labels)

        B_points = [i for i, x in enumerate(labels) if x.startswith('B-')]
        if B_points[-1] != len(labels):
            B_points += [len(labels)]
        # print(B_points)

        entity_list = []
        for i, b in enumerate(B_points[:-1]):
            entity_type = labels[b].split('-')[-1]
            span_left, span_right = b, b        # left & right pointer of an entity span
            for j in range(span_left, B_points[i + 1]):
                if labels[j].split('-')[-1] == entity_type:
                    span_right = j
            # end for
            entity_text = ' '.join([tok for tok in words[span_left: span_right + 1]])

            d = dict(
                text=entity_text,
                type=entity_type,
                start_token=span_left,
                end_token=span_right,
            )
            entity_list.append(d)
        # end for

        return entity_list


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--input', type=FileType('r'), help='3-column NER outputs')
    parser.add_argument('--output', type=FileType('w'),
                        help='Output tsv file for relation classification.')

    return parser.parse_args()


def main():
    args = arg_parse()

    transformer = NEROutputTransformer()
    docs = transformer.read_file(args.input.name)

    transformed = transformer.transform(docs)
    pprint(transformed[0])

    writer = csv.DictWriter(args.output, fieldnames=['docid', 'text_a'], delimiter='\t')
    writer.writeheader()
    for d in transformed:
        writer.writerow(d)
    # end for
    print('File written to %s' % args.output.name)




if __name__ == '__main__':
    main()
