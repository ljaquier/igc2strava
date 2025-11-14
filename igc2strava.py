from xc_scorer import XCScorer, IGCParser
from datetime import datetime, timezone
from gpx2strava import gpx2strava, utils


def get_details(igc_parser, tracklog):
    scoring_rules = {
        "flat": {"multiplier": 1.2},
        "FAI": {"multiplier": 1.4},
        "closedFAI": {"multiplier": 1.6},
        "closedFlat": {"multiplier": 1.4},
        "freeFlight": {"multiplier": 1.0},
        "outReturn": {"multiplier": 1.2}
    }
    scorer = XCScorer(tracklog, scoring_rules)
    score = scorer.score_flight(track_optimization=True)

    return {
        'score': score['score'],
        'distance': score['properties']['total_distance'],
        'type': score['triangle_type'] if score['type'] == 'triangle' else score['type'],
        'glider': igc_parser.glider_type,
        'lowest_point': min(tracklog, key=lambda point: point.alt),
        'highest_point': max(tracklog, key=lambda point: point.alt),
        'first_point': tracklog[0],
        'last_point': tracklog[-1]
    }

def get_title(details):
    types = {
        "flat": "Flat triangle",
        "FAI": "FAI triangle",
        "closedFAI": "Closed FAI triangle",
        "closedFlat": "Closed flat triangle",
        "free_distance": "Free flight"
    }
    return f"🪂 Paragliding / {types[details['type']]}"

def get_description(details):
    return (
        f"XC distance: {details['distance']:.2f} km\n"
        f"XC score: {details['score']:.2f} pts\n"
        +
        (f"Glider: {details['glider']}\n" if details['glider'] else "")
        +
        "\n"
        f"Takeoff: {details['first_point'].alt:.0f} m\n"
        f"Max alt.: {details['highest_point'].alt:.0f} m\n"
        f"Min alt.: {details['lowest_point'].alt:.0f} m\n"
        f"Landing: {details['last_point'].alt:.0f} m"
    )

def get_gpx(igc_parser, tracklog):
    details = get_details(igc_parser, tracklog)

    track_points = []
    for point in tracklog:
        track_points.append(
            gpx2strava.TrackPoint(
                point.lat,
                point.lon,
                point.alt,
                datetime.combine(igc_parser.date, point.time, timezone.utc)
            )
        )

    return gpx2strava.get_gpx(
        get_title(details),
        get_description(details),
        'Workout',
        track_points
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Create an activity on Strava from a paragliding flight')
    parser.add_argument('config_file', nargs='?', help='Config file')
    parser.add_argument('igc_file', nargs='?', help='IGC file')

    args = parser.parse_args()

    if args.config_file and args.igc_file:
        config = utils.load_json(args.config_file)

        igc_parser = IGCParser(args.igc_file)
        tracklog = igc_parser.parse()

        response = gpx2strava.upload_to_strava(gpx2strava.get_access_token(config), get_gpx(igc_parser, tracklog))
        print(f"{args.igc_file} : {response.status_code} : {response.text}")

        utils.save_json(args.config_file, config)
    else:
        parser.print_help()
