"""
This file contains some basic data processing utility functions. 
Can be run as a script to either repair unfinished data, merge data
or load data from files into the main ChatGPT script. 
"""

import pandas as pd
import data_querying
from argparse import ArgumentParser
from revChatGPT.V1 import Chatbot

def concat_cols(row, cols):
    string = ''
    for col in cols:
        string += row[col] + ' '
    return string.strip()



def process_prompt(prompt):
    return prompt.replace('[ WP ]', '').replace('[ OT ]', '')


def process_spaces(story):
    return story.replace(
        ' ,', ',').replace(
        ' .', '.').replace(
        ' ?', '?').replace(
        ' !', '!').replace(
        ' ;', ';').replace(
        ' \'', '\'').replace(
        ' ’ ', '\'').replace(
        ' :', ':').replace(
        '<newline>', '\n').replace(
        '`` ', '"').replace(
        ' \'\'', '"').replace(
        '\'\'', '"').replace(
        '.. ', '... ').replace(
        ' )', ')').replace(
        '( ', '(').replace(
        ' n\'t', 'n\'t').replace(
        ' i ', ' I ').replace(
        ' i\'', ' I\'').replace(
        '\\\'', '\'').replace(
        '\n ', '\n').strip()


def repair_dataframe(data: pd.DataFrame, chatbot: Chatbot, verbose=False):
    """
    TODO: UPDATE WITH THE CHATGPT API!
    DESC: Repair dataframe that has incomplete responses from ChatGPT.
    PARAMS:
    data: a dataFrame that has both a 'prompts' and 'responses' column
    chatbot: logged in ChatGPT
    verbose: print chatGPT's responses while querying 
    """
    fail = 0
    count = 0
    for _, row in data.iterrows():
        if row['responses'] == data_querying.FAILSTRING:
            try: 
                prompt = row['prompts']
                response = data_querying.prompt_ChatGPT(prompt, chatbot)
                row['responses'] = response
                if verbose:
                    print(f'{prompt}:{response}')
                count += 1
                chatbot.reset_chat()
                chatbot.clear_conversations()
            except:
                print(f'The prompt: {prompt} did not successfully get a response from ChatGPT.\n')
                fail += 1
                continue
    print(f'Successfully got {count} responses from ChatGPT, failed to get {fail} responses.')
    return data



def merge_human_sampled(original_file, original_cols, sampled_file, sampled_cols, outfile=None):
    """
    DESC: Given files of both original and sampled data,
    merge them into one dataFrame.
    PARAMS: 
    original_file, sampled_file: file of human data, chatGPT data resp.
    original_cols, sampled_cols: list of cols to read in from original_file, sampled_file resp. 
        if there are multiple columns, they're concatenated with a space separating the strings in each.
    outfile: where to write merged data
    RETURNS: dataFrame of merged data
    """
    original = pd.read_csv(original_file)
    sampled = pd.read_csv(sampled_file)
    
    if original_cols is None:
        original_cols = original.columns
    if sampled_cols is None:
        sampled_cols = sampled.columns

    original['original'] = original.apply(lambda row: concat_cols(row, original_cols), axis=1)
    sampled['sampled'] = sampled.apply(lambda row: concat_cols(row, sampled_cols), axis=1)
    df = pd.concat([original['original'], sampled['sampled']], axis=1)
    if outfile:
        df.to_csv(outfile, index=False)
    return df


def strip_text(file, col, strip_msg):
    df = pd.read_csv(file)
    assert col in df.columns, 'invalid column called for this dataFrame'
    df[col] = df.apply(lambda row: row[col].replace(strip_msg, ''), axis=1)
    df.to_csv(file, index=False)
    print(f'Stripped the text \'{strip_msg}\' from {file} in column {col}')
    




if __name__=='__main__':
    parser = ArgumentParser(prog='process data already retrieved, in different ways')
    parser.add_argument('task', help='what you want to do', choices=['merge', 'repair', 'strip'])
    merge = parser.add_argument_group()
    merge.add_argument('--orig_file', help='file with human data')
    merge.add_argument('--orig_cols', help='cols to grab from orig_file', type=str)
    merge.add_argument('--sampled_file', help='file with ChatGPT data')
    merge.add_argument('--sampled_cols', help='cols to grab from data', type=str)
    merge.add_argument('--outfile', help='where to store new merged data')
    repair = parser.add_argument_group()
    repair.add_argument('--repair_file', nargs=1, help='file with data that needs to be repaired')
    repair.add_argument('--email', nargs=1, help='for ChatGPT login')
    repair.add_argument('--password', nargs=1),
    repair.add_argument('--paid', action='store_true', help='specify if acct holder has paid ChatGPT')
    strip = parser.add_argument_group()
    strip.add_argument('--strip_file', help='file to strip from')
    strip.add_argument('--strip_col', help='col to strip from')
    strip.add_argument('--strip_msg', help='text to strip')

    parser.add_argument('-v', '--verbose', action='store_true', help='print while doing stuff')
    args = parser.parse_args()

    if args.task == 'merge':
        assert args.orig_file and args.sampled_file, 'need to have files to merge!'
        orig_cols = args.orig_cols.split(', ')
        sampled_cols = args.sampled_cols.split(', ')
        merged = merge_human_sampled(args.orig_file, orig_cols, args.sampled_file, sampled_cols, args.outfile)
    

    elif args.task == 'repair':
        broken = pd.read_csv(args.repair_file)
        fixed = repair_dataframe(broken, data_querying.init_ChatGPT(args.email, args.password, args.paid))
        fixed.to_csv(args.repair_file, index=False)

    elif args.task == 'strip':
        assert args.strip_file and args.strip_col and args.strip_msg
        strip_text(args.strip_file, args.strip_col, args.strip_msg)


