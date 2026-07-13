from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TweetAuthor:
    id: str = ""
    name: str = ""
    screen_name: str = ""
    avatar_url: str = ""

@dataclass
class TweetMedia:
    url: str = ""
    width: int = 0
    height: int = 0
    type: str = "photo"  # photo | video

@dataclass
class TweetItem:
    id: str
    url: str = ""
    author: TweetAuthor = field(default_factory=TweetAuthor)
    text: str = ""
    created_at: str = ""
    media: List[TweetMedia] = field(default_factory=list)
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    is_reply: bool = False
    parent_id: Optional[str] = None

    translated_text: str = ""
    is_valuable: bool = True

@dataclass
class TweetConversation:
    root: Optional[TweetItem] = None
    ancestors: List[TweetItem] = field(default_factory=list)
    target: Optional[TweetItem] = None
    quote: Optional[TweetItem] = None
    replies: List[TweetItem] = field(default_factory=list)
