import logging
import os

from dotenv import load_dotenv

from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig
from tinygrid.ercot.archive import ERCOTArchiveBundle

load_dotenv()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

DEBUG = False


def main():
    auth = ERCOTAuth(
        ERCOTAuthConfig(
            username=os.getenv("ERCOT_USERNAME"),
            password=os.getenv("ERCOT_PASSWORD"),
            subscription_key=os.getenv("ERCOT_SUBSCRIPTION_KEY"),
        )
    )

    ercot = ERCOT(auth=auth)

    logger.info("TEST get_60_day_dam_disclosure")
    reports = ercot.get_60_day_dam_disclosure("2025-10-30")
    for name, df in reports.items():
        logger.debug(f"{name}")
        logger.debug(df.head())
        logger.debug("*" * 30)

    logger.info("TEST get_60_day_dam_disclosure")
    reports = ercot.get_60_day_sced_disclosure("2025-10-30")
    logger.debug(reports)

    start_ts = "2025-12-20"
    end_ts = "2025-12-30"

    logger.info("TEST get_system_wide_actuals")
    results = ercot.get_system_wide_actuals(start=start_ts, end=end_ts)
    logger.info(results.head())
    logger.debug(results)

    logger.info("TEST get_se_load")
    results = ercot.get_se_load(start=start_ts, end=end_ts)
    logger.debug(results)

    logger.info("TEST get_se_dc_tie_flows")
    results = ercot.get_se_dc_tie_flows(start_ts, end_ts)
    logger.debug(results)

    bundle_client = ERCOTArchiveBundle(ercot=ercot)
    bundles = bundle_client.bundles("NP4-33-CD")
    for bundle_link in bundles.links:
        logger.debug(f"{bundle_link = }")
        logger.debug("*" * 30)

    dfs = bundle_client.one_bundle(bundles.links[0])
    logger.debug(dfs)


if __name__ == "__main__":
    main()
