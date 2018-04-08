import sys

from urllib.parse import urlsplit

from transmissionrpc import Client

from clients.torrentclient import TorrentClient


class TransmissionClient(TorrentClient):

    def __init__(self, logger, username=None, password=None, url=None, hostname=None):

        TorrentClient.__init__(self, logger, username=username, password=password, url=url, hostname=hostname)
        self.torrent_client = 'transmission'
        self._authenticate()
        self.rtorrent = None
        self._authenticate()

    def _authenticate(self):
        """
        Setup connection to rTorrent XMLRPC server
        :return:
        """

        try:
            self.transmission = Client(self.url, user=self.username, password=self.password)
        except ConnectionRefusedError as e:
            self.send_log('Failed to connect to transmission.  Aborting', 'critical')
            sys.exit(1)

        self.send_log('Successfully connected to transmission', 'info')

    def _build_torrent_list(self, torrents):
        """
        Take the resulting torrent list and create a consistent structure shared through all clients
        :return:
        """
        self.send_log('Structuring list of torrents', 'debug')

        for torrent in torrents:
            total_seeds = 0
            for item in torrent.trackerStats:
                total_seeds = total_seeds + item['seederCount']

            tracker_hostname = urlsplit(torrent.trackerStats[0]['host']).hostname
            tracker_name = self._get_tracker_name(tracker_hostname)

            self.torrent_list[torrent.hashString] = {}
            self.torrent_list[torrent.hashString]['name'] = torrent.name
            self.torrent_list[torrent.hashString]['total_size'] = torrent.totalSize
            self.torrent_list[torrent.hashString]['progress'] = torrent.progress
            self.torrent_list[torrent.hashString]['total_downloaded'] = torrent.downloadedEver
            self.torrent_list[torrent.hashString]['total_uploaded'] = torrent.uploadedEver
            self.torrent_list[torrent.hashString]['ratio'] = torrent.ratio
            self.torrent_list[torrent.hashString]['total_seeds'] = total_seeds
            self.torrent_list[torrent.hashString]['state'] = torrent.status
            self.torrent_list[torrent.hashString]['tracker'] = tracker_name
            self.torrent_list[torrent.hashString]['total_files'] = len(torrent.files())

    def _get_tracker_name(self, hostname):
        """
        Returns a 'nice' tracker hostname

        Some trackers use tracker.domain or announce.domain
        and this looked ugly in grafana.

        Code taken from the transmission javascript as they do more or less the same.
        """
        dot = hostname.find('.')
        lastdot = hostname.rfind('.')
        if dot != lastdot:
            hostname = hostname[(dot + 1):]

        return hostname

    def get_all_torrents(self):
        """
        Return list of all torrents
        :return:
        """
        self._authenticate()
        self._build_torrent_list(self.transmission.get_torrents())
