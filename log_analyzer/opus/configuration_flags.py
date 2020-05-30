from enum import Flag, auto
from typing import Sequence


class InfoFlags(Flag):
    PERFORMED_SEARCH = auto()
    DID_NOT_PERFORM_SEARCH = auto()
    VIEWED_BROWSE_TAB_AS_GALLERY = auto()
    VIEWED_BROWSE_TAB_AS_TABLE = auto()
    VIEWED_CART_TAB_AS_GALLERY = auto()
    VIEWED_CART_TAB_AS_TABLE = auto()
    VIEWED_DETAIL_TAB = auto()
    VIEWED_SLIDE_SHOW = auto()
    VIEWED_SELECT_METADATA = auto()
    CHANGED_SELECTED_METADATA = auto()
    CHANGED_SORT_ORDER = auto()
    DOWNLOADED_CSV_FILE_FOR_ALL_RESULTS = auto()
    DOWNLOADED_CSV_FILE_FOR_ONE_OBSERVATION = auto()
    DOWNLOADED_ZIP_FILE_FOR_ONE_OBSERVATION = auto()
    DOWNLOADED_ZIP_URL_FILE_FOR_ONE_OBSERVATION = auto()
    DOWNLOADED_CSV_FILE_FOR_CART = auto()
    DOWNLOADED_ZIP_ARCHIVE_FILE_FOR_CART = auto()
    DOWNLOADED_ZIP_URL_FILE_FOR_CART = auto()
    VIEWED_HELP_FILE = auto()
    VIEWED_HELP_FILE_AS_PDF = auto()
    HAS_OBSOLETE_SLUG = auto()

    def get_fancy_name(self) -> str:
        name = self.name.lower().replace("_", " ")\
            .replace("csv", "CSV").replace("zip", "ZIP").replace('pdf', "PDF").replace('url', 'URL')
        return name[0].upper() + name[1:]

    def as_list(self) -> Sequence['InfoFlags']:
        return [flag for flag in InfoFlags if flag in self]


class IconFlags(Flag):
    HAS_SEARCH = auto()
    FETCHED_GALLERY = auto()
    HAS_METADATA = auto()
    HAS_DOWNLOAD = auto()
    HAS_OBSOLETE_SLUG = auto()
