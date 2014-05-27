__author__ = 'user'

import threading
import binascii
from time import time

# Setup logger
import logging
_logger = logging.getLogger(__name__)

# Tribler defs
from Tribler.Core.simpledefs import NTFY_MISC, NTFY_TORRENTS, NTFY_MYPREFERENCES, \
    NTFY_VOTECAST, NTFY_CHANNELCAST, NTFY_METADATA, \
    DLSTATUS_METADATA, DLSTATUS_WAITING4HASHCHECK

# DB Tuples
from RpcDBTuples import Torrent, ChannelTorrent, RemoteChannelTorrent, RemoteTorrent

# Tribler communities
from Tribler.community.search.community import SearchCommunity
from Tribler.community.allchannel.community import AllChannelCommunity
#from Tribler.community.channel.community import ChannelCommunity
#from Tribler.community.channel.preview import PreviewChannelCommunity
#from Tribler.community.metadata.community import MetadataCommunity

from Tribler.Core.Search.SearchManager import split_into_keywords

from Tribler.community.channel.community import ChannelCommunity, \
    forceDispersyThread, forcePrioDispersyThread, warnDispersyThread


class TorrentManager():
    connected = False

    _session = None
    _dispersy = None
    _remote_lock = None

    _misc_db = None
    _torrent_db = None
    _channelcast_db = None
    _votecast_db = None

    _channel_keywords = []
    _channel_results = []

    _torrent_keywords = []
    _torrent_results = []

    def __init__(self, session, xmlrpc=None):
        self.connected = False

        self._session = session
        self._remote_lock = threading.Lock()

        self._connect()

        if xmlrpc:
            self._xmlrpc_register(xmlrpc)

    def _connect(self):
        if not self.connected:
            self.connected = True
            self._misc_db = self._session.open_dbhandler(NTFY_MISC)
            self._torrent_db = self._session.open_dbhandler(NTFY_TORRENTS)
            self._channelcast_db = self._session.open_dbhandler(NTFY_CHANNELCAST)
            self._votecast_db = self._session.open_dbhandler(NTFY_VOTECAST)

            self._dispersy = self._session.lm.dispersy
        else:
            raise RuntimeError('ChannelManager already connected')

    def search_channel_local_mock(self, filter):
        return [{"name": "Channel 1", "stars": 3, "torrents": 20},
                {"name": "Channel 2", "stars": 1, "torrents": 23},
                {"name": "Channel 3", "stars": 5, "torrents": 42}]

    def _xmlrpc_register(self, xmlrpc):
        xmlrpc.register_function(self.get_local, "torrents.get_local")
        xmlrpc.register_function(self.search_remote, "torrents.search_remote")
        xmlrpc.register_function(self.get_remote_results_count, "torrents.get_remote_results_count")
        xmlrpc.register_function(self.get_remote_results, "torrents.get_remote_results")
        #xmlrpc.register_function(self.get_by_channel, "torrents.get_by_channel")
        xmlrpc.register_function(self.get_full_info, "torrents.get_full_info")




    def get_local(self, filter):
        pass

    @forceDispersyThread
    def search_remote(self, keywords):
        try:
            self._set_keywords(keywords)
        except:
            return False

        nr_requests_made = 0

        if self._dispersy:
            for community in self._dispersy.get_communities():
                if isinstance(community, SearchCommunity):
                    nr_requests_made = community.create_search(self._torrent_keywords, self._search_remote_callback)
                    if not nr_requests_made:
                        _logger.error("@@@@ Could not send search in SearchCommunity, no verified candidates found")
                    break

            else:
                _logger.error("@@@@ Could not send search in SearchCommunity, community not found")

        else:
            _logger.error("@@@@ Could not send search in SearchCommunity, Dispersy not found")

        _logger.info("@@@@ Made %s requests to the search community" % nr_requests_made)

        return 44 #nr_requests_made


    @forceDispersyThread
    def _search_remote_callback(self, keywords, results, candidate):
#        try:
        print "******************** TorrentSearchGridManager: gotRemoteHist: got %s unfiltered results for %s %s %s" % (len(results), keywords, candidate, time())

        #for t in results:
        #    print "************ %s" % str(t)

        # Ignore searches we don't want (anymore)
        if not self._torrent_keywords == keywords:
            return

        try:
            self._remote_lock.acquire()

            for result in results:
                categories = result[4]
                category_id = self._misc_db.categoryName2Id(categories)

                remoteHit = RemoteTorrent(-1, result[0], result[8], result[9], result[1], result[2], category_id, self._misc_db.torrentStatusName2Id(u'good'), result[6], result[7], set([candidate]))
                print unicode(remoteHit.name)

                # Guess matches
                #keywordset = set(keywords)
                #swarmnameset = set(split_into_keywords(remoteHit.name))
                #matches = {'fileextensions': set()}
                #matches['swarmname'] = swarmnameset & keywordset  # all keywords matching in swarmname
                #matches['filenames'] = keywordset - matches['swarmname']  # remaining keywords should thus me matching in filenames or fileextensions

                #if len(matches['filenames']) == 0:
                #    _, ext = os.path.splitext(result[0])
                #    ext = ext[1:]

                #    matches['filenames'] = matches['swarmname']
                #    matches['filenames'].discard(ext)

                #    if ext in keywordset:
                #        matches['fileextensions'].add(ext)
                #remoteHit.assignRelevance(matches)
                remoteHit.misc_db = self._misc_db
                remoteHit.torrent_db = self._torrent_db
                remoteHit.channelcast_db = self._channelcast_db

                self._torrent_results.append(remoteHit)

        finally:
            self._remote_lock.release()
        return


    def get_remote_results(self):
        count = max(len(self._torrent_results), 10)
        return self._prepare_torrents(self._torrent_results[0:count])

    def get_remote_results_count(self):
        return len(self._torrent_results)

    def get_full_info(self):
        pass

    def _set_keywords(self, keywords):
        keywords = split_into_keywords(unicode(keywords))
        keywords = [keyword for keyword in keywords if len(keyword) > 1]

        if keywords == self._torrent_keywords:
            return True

        try:
            self._remote_lock.acquire()

            self._torrent_keywords = keywords
            self._torrent_results = []
        finally:
            self._remote_lock.release()

        return True

    def _prepare_torrents(self, trs):
        torrents = []
        for tr in trs:
            try:
                torrents.append(self._prepare_torrent(tr))
            except:
                _logger.error("prepare torrent fail: %s" % tr.name)
                pass

        return torrents

    def _prepare_torrent(self, tr):
        assert isinstance(tr, RemoteTorrent)

        return {'infohash': binascii.hexlify(tr.infohash).upper() if tr.infohash else False,
                'swift_hash': binascii.hexlify(tr.swift_hash).upper() if tr.swift_hash else False,
                'swift_torrent_hash': binascii.hexlify(tr.swift_torrent_hash).upper() if tr.swift_torrent_hash else False,
                'torrent_file_name': tr.torrent_file_name or False,
                'name': tr.name,
                #'length': tr.length,
                'category_id': tr.category_id,
                'status_id': tr.status_id,
                'num_seeders': tr.num_seeders,
                'num_leechers': tr.num_leechers,
                }

    """
        self.infohash = infohash
        self.swift_hash = swift_hash
        self.swift_torrent_hash = swift_torrent_hash
        self.torrent_file_name = torrent_file_name
        self.name = name
        self.length = length or 0
        self.category_id = category_id
        self.status_id = status_id

        self.num_seeders = num_seeders or 0
        self.num_leechers = num_leechers or 0

        self.update_torrent_id(torrent_id)
        self.updateChannel(channel)

        self.channeltorrents_id = None
        self.misc_db = None
        self.torrent_db = None
        self.channelcast_db = None
        self.metadata_db = None

        self.relevance_score = None
        self.query_candidates = None
        self._progress = None
        self.dslist = None
        self.magnetstatus = None
    """