from metrico.database import models


class Analyzer:
    ...


def get_lost(media: models.Media):
    last_stats, lost = None, [0, 0, 0]
    for stat in media.stats:
        if last_stats:
            value = [
                last_stats[0] - stat.comments,
                last_stats[1] - stat.likes,
                last_stats[2] - stat.views,
            ]
            for i in range(3):
                if value[i] < 0:
                    lost[i] += -value[i]

        last_stats = [stat.comments, stat.likes, stat.views]

    return lost
