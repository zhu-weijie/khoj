# External Packages
import torch
import json

# Internal Packages
from src.processor.ledger.beancount_to_jsonl import beancount_to_jsonl
from src.processor.markdown.markdown_to_jsonl import markdown_to_jsonl
from src.processor.org_mode.org_to_jsonl import org_to_jsonl
from src.search_type import image_search, text_search
from src.utils.config import SearchType, SearchModels, ProcessorConfigModel, ConversationProcessorConfigModel
from src.utils import state
from src.utils.helpers import get_absolute_path
from src.utils.rawconfig import FullConfig, ProcessorConfig


def configure_server(args):
    # Stores the file path to the config file.
    state.config_file = args.config_file

    # Store the raw config data.
    state.config = args.config

    # Store the verbose flag
    state.verbose = args.verbose

    # Initialize the search model from Config
    state.model = configure_search(state.model, args.config, args.regenerate, device=state.device, verbose=state.verbose)

    # Initialize Processor from Config
    state.processor_config = configure_processor(args.config.processor, verbose=state.verbose)

    return args.host, args.port, args.socket


def configure_search(model: SearchModels, config: FullConfig, regenerate: bool, t: SearchType = None, device=torch.device("cpu"), verbose: int = 0):
    # Initialize Org Notes Search
    if (t == SearchType.Org or t == None) and config.content_type.org:
        # Extract Entries, Generate Notes Embeddings
        model.orgmode_search = text_search.setup(org_to_jsonl, config.content_type.org, search_config=config.search_type.asymmetric, regenerate=regenerate, device=device, verbose=verbose)

    # Initialize Org Music Search
    if (t == SearchType.Music or t == None) and config.content_type.music:
        # Extract Entries, Generate Music Embeddings
        model.music_search = text_search.setup(org_to_jsonl, config.content_type.music, search_config=config.search_type.asymmetric, regenerate=regenerate, device=device, verbose=verbose)

    # Initialize Markdown Search
    if (t == SearchType.Markdown or t == None) and config.content_type.markdown:
        # Extract Entries, Generate Markdown Embeddings
        model.markdown_search = text_search.setup(markdown_to_jsonl, config.content_type.markdown, search_config=config.search_type.asymmetric, regenerate=regenerate, device=device, verbose=verbose)

    # Initialize Ledger Search
    if (t == SearchType.Ledger or t == None) and config.content_type.ledger:
        # Extract Entries, Generate Ledger Embeddings
        model.ledger_search = text_search.setup(beancount_to_jsonl, config.content_type.ledger, search_config=config.search_type.symmetric, regenerate=regenerate, verbose=verbose)

    # Initialize Image Search
    if (t == SearchType.Image or t == None) and config.content_type.image:
        # Extract Entries, Generate Image Embeddings
        model.image_search = image_search.setup(config.content_type.image, search_config=config.search_type.image, regenerate=regenerate, verbose=verbose)

    return model


def configure_processor(processor_config: ProcessorConfig, verbose: int):
    if not processor_config:
        return

    processor = ProcessorConfigModel()

    # Initialize Conversation Processor
    processor.conversation = configure_conversation_processor(processor_config.conversation, verbose)

    return processor


def configure_conversation_processor(conversation_processor_config, verbose: int):
    conversation_processor = ConversationProcessorConfigModel(conversation_processor_config, verbose)

    conversation_logfile = conversation_processor.conversation_logfile
    if conversation_processor.verbose:
        print('INFO:\tLoading conversation logs from disk...')

    if conversation_logfile.expanduser().absolute().is_file():
        # Load Metadata Logs from Conversation Logfile
        with open(get_absolute_path(conversation_logfile), 'r') as f:
            conversation_processor.meta_log = json.load(f)

        print('INFO:\tConversation logs loaded from disk.')
    else:
        # Initialize Conversation Logs
        conversation_processor.meta_log = {}
        conversation_processor.chat_session = ""

    return conversation_processor