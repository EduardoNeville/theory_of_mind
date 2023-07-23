import json
from argparse import ArgumentParser
from csv import DictReader
from pathlib import Path


def update_data_and_file(new_record_id: int, new_record: dict,
                         output_data: dict[int,
                                           dict], output_file: Path) -> None:
    """Update output record and file. Updating file after every input makes it
    safe if program ends suddenly or user quits early
    """
    output_data[new_record_id] = new_record
    json.dump(output_data, output_file.open('w'))


def get_missing_classifications(
        output_data: dict[int, dict]) -> dict[int, str]:
    """Build dictionary of reaons user has input for the model incorrectly
    answering questions
    """
    missing_classifications = set()
    for record in output_data.values():
        if record['correct']:
            continue

        missing_classifications.add(record['classification'])

    return {i: mc for i, mc in enumerate(sorted(missing_classifications))}


def print_missing_classifications(
        missing_classifications: dict[int, str]) -> None:
    """Helper function that prints a table showing the reasons a user has input
    for a question being missed so far. Allows the user to just use indices for
    subequent questions missed rather than having to type the reason every time
    """
    if len(missing_classifications) == 0:
        print("No missing classifications yet...")
        print("classify the reason; the first time you'll need to type it out")
        print(
            "after you have used a reason once, you can use the printed index")
        print("or type a new answer that will be added to the list next run")
        return

    print("Current Missing Classifications: ")
    for i, mc in missing_classifications.items():
        print(f"  {i}: {mc}")


def process_file(file: Path, output_data: dict[int, dict],
                 output_file: Path) -> None:
    """Execute loop for classifying why all missed questions in a given output
    file were missed
    """
    print(f"Running File {file.name}")
    with file.open('r') as csv_file:
        csv_reader = DictReader(csv_file)
        for i, line in enumerate(csv_reader):
            line_output = line.copy()
            row_id = f"{file.name}_{i}"
            print(row_id)

            answer = line['answer'].strip().lower()
            gpt_answer = line['gpt_answer'].strip().lower()
            model_correct = answer == gpt_answer

            if model_correct:
                line_output['correct'] = True
                line_output['classification'] = 'model_correct'
                update_data_and_file(row_id, line_output, output_data,
                                     output_file)
                continue

            # display the actions and question so that user can read them
            print(f"file {file.name}, line {i+1}")
            print(line['actions'])
            print(line['question'])
            print(f"RIGHT ANSWER: {line['answer']},"
                  f"GPT ANSWER: {line['gpt_answer']}")
            print(line['gpt_response'])

            # prompt the user for the classification of why the model was wrong
            missing_classifications = get_missing_classifications(output_data)
            print_missing_classifications(missing_classifications)
            line_output['correct'] = False
            classification = input("Classify why the answer is wrong:")

            # if they return something int like, assume it's an index into the
            # list holding their prior classifications; otherwise, just use
            # the raw string as the classification
            try:
                classification_id = int(classification)
                line_output['classification'] = missing_classifications[
                    classification_id]
            except ValueError:
                line_output['classification'] = classification.strip()

            update_data_and_file(row_id, line_output, output_data, output_file)

            print('-' * 80)


def main(file_pattern: str, data_dir: Path, output_file: Path) -> None:
    """Iterate over all the files in the output directory and classify why the
    model missed the incorrect answers using the reasoning it provided
    """
    try:
        output_data = json.load(output_file.open('r'))
    except FileNotFoundError:
        output_data = {}

    data_dir_path = Path(data_dir)
    for file_path in data_dir_path.glob(file_pattern):
        process_file(file_path, output_data, output_file)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        '-fp',
        '--file_pattern',
        type=str,
        default='*',
        required=False,
        help=
        'The file pattern used by pathlib.Path to glob over files in a directory. Default is *.'
    )
    parser.add_argument(
        '-d',
        '--data_dir',
        type=Path,
        default='./data/raw_output',
        required=False,
        help=
        'The directory where we apply the glob. Default is ./data/raw_output.')
    parser.add_argument(
        '-o',
        '--output_file',
        type=Path,
        default='./data/classified_results.json',
        required=False,
        help=
        'Path to the current output file. Default is ./data/classified_results.json '
    )

    args = parser.parse_args()
    main(args.file_pattern, args.data_dir, args.output_file)
