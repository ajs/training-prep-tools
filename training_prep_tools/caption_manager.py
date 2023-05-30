"""A quick and dirty YAML-based caption creator"""

import argparse
import logging
import os
import pathlib
from typing import Dict, Optional

import yaml

VARIADIC_ARG = 'store'
BOOLEAN_ARG = 'store_true'
CONST_ARG = 'store_const'


def is_image(filename: pathlib.Path) -> bool:
    """Is the file an image?"""
    ext = fname_ext(filename)
    if not ext:
        return False
    if ext.lower() in {'png', 'jpg', 'jpeg', 'tiff', 'tif'}:
        return True
    return False


def fname_parts(filename: os.PathLike) -> tuple:
    """Return the base filename and extension as a tuple"""
    return tuple(str(filename).rsplit('.', 1))


def fname_base(filename: os.PathLike) -> str:
    """Just the filename without the extension (doesn't remove directory)"""
    return fname_parts(filename)[0]


def fname_ext(filename: os.PathLike) -> Optional[str]:
    """Just the file extension"""
    parts = fname_parts(filename)
    if len(parts) > 1:
        return parts[-1]
    return None


def make_caption(config_values: Dict[str, str]) -> str:
    """Create the caption string from the merged configuration dict"""
    params = config_values.copy()
    if 'required' in config_values:
        required = [field.strip() for field in config_values['required'].split(',')]
        params.update({name: config_values.get(name, "") for name in required})
    else:
        required = []

    if config_values.get('caption'):
        caption = config_values['caption'].format(**params)
        if config_values.get('keywords'):
            keywords = config_values['keywords'].strip()
            if keywords:
                caption = caption.rstrip() + ', ' + keywords.strip()
    elif config_values.get('keywords'):
        caption = config_values['keywords']
    elif required:
        caption = ", ".join(f"{field} is {params[field]}" for field in required)
    elif 'desc' in config_values:
        caption = config_values['desc']
    else:
        caption = ", ".join(f"{field} is {value}" for field, value in config_values.items())

    return caption


def write_caption_file(caption_file: pathlib.Path, config_values: Dict[str, str]):
    """Write the caption file"""
    with caption_file.open('w') as caption_fh:
        caption_fh.write(make_caption(config_values))


def process_image_file(image_path: pathlib.Path, target_dir: pathlib.Path, config_values: Dict[str, str]):
    """Given a file and target directory, write the given config values as a caption"""
    base_file = str(image_path).rsplit('.', 1)[0]
    caption_file = target_dir.joinpath(pathlib.Path(base_file + '.txt').name)
    yaml_file = pathlib.Path(base_file + '.yaml')
    if yaml_file.exists():
        config_values = config_values.copy()
        config_values.update(get_yaml_contents(yaml_file))
    write_caption_file(caption_file, config_values)


def get_yaml_contents(yaml_file: pathlib.Path):
    """Read the YAML file and return the contents, format errors to include filename"""
    try:
        with yaml_file.open('r') as yaml_fh:
            return yaml.safe_load(yaml_fh)
    except yaml.YAMLError as err:

        raise ValueError(f"Unable to read YAML file, {yaml_file}: {err!r}") from err


def process_source_tree(
        source: pathlib.Path,
        target: pathlib.Path,
        config_values: Dict[str, str] | None = None,
        preserve_captions: bool = False,
        flat_target: bool = False,
) -> None:
    """Read files from source and write captions to target"""

    target.mkdir(parents=True, exist_ok=True)
    config_values = config_values or {}
    caption_config = source.joinpath('caption_config.yaml')
    if caption_config.is_file():
        with caption_config.open('r') as caption_fh:
            try:
                new_config = yaml.safe_load(caption_fh)
            except yaml.YAMLError as err:
                raise ValueError(f"Unable to read YAML file, {caption_config}: {err!r}") from err
        if 'keywords' in new_config and 'keywords' in config_values:
            current_keywords = [keyword.strip() for keyword in config_values['keywords'].split(',')]
            new_keywords = [keyword.strip() for keyword in new_config['keywords'].split(',')]
            new_config['keywords'] = ', '.join(keyword for keyword in new_keywords + current_keywords if keyword)
        config_values.update(new_config)
    for filepath in source.iterdir():
        if filepath.is_dir():
            logging.info("Processing subdir: %s...", filepath)
            next_target = target if flat_target else target.joinpath(os.path.basename(filepath))
            process_source_tree(
                filepath, next_target,
                config_values=config_values.copy(),
                preserve_captions=preserve_captions,
                flat_target=flat_target,
            )
        elif str(filepath).rsplit('.', 1)[-1].lower() == 'yaml':
            continue
        elif is_image(filepath):
            process_image_file(filepath, target, config_values)
        else:
            logging.debug("Skipping non-image: %s", filepath)
            continue


def main():
    """Main body"""

    parser = argparse.ArgumentParser(
        'caption-manager',
        description='Manage image captions based on YAML configs in a directory tree',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    verbose_help = "Turn on verbose logging output"
    parser.add_argument('-v', '--verbose', action=CONST_ARG, dest='loglevel', const=logging.INFO, help=verbose_help)
    debug_help = "Turn on debug logging output (implies --verbose)"
    parser.add_argument('-d', '--debug', action=CONST_ARG, dest='loglevel', const=logging.DEBUG, help=debug_help)
    target_help = "Directory tree to place the resulting captions in"
    parser.add_argument('-t', '--target', action=VARIADIC_ARG, metavar='DIRECTORY', type=pathlib.Path, help=target_help)
    flat_help = "Flatten the tree found in source int the single-level target"
    parser.add_argument('-f', '--flat-target', action=BOOLEAN_ARG, help=flat_help)
    source_dir_help = "A source directory to find images and caption configs in"
    parser.add_argument('source', action=VARIADIC_ARG, nargs='+', type=pathlib.Path, help=source_dir_help)
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel or logging.WARNING)

    for source in args.source:
        if source == '.':
            source = os.getcwd()
        target = args.target or source
        process_source_tree(pathlib.Path(source), pathlib.Path(target), flat_target=args.flat_target)


if __name__ == '__main__':
    main()
