import logging

from single_runner import run_once
from config import load_config, VIDEO
from video import create_ffmpeg_container, restart_nginx, create_nginx_with_trace

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logger = logging.getLogger("batch_runner")

if __name__ == "__main__":
    exp_list, total_count, total_duration = load_config()

    logger.info("Total experiment count: {}, duration: {} seconds ({} hours)".format(total_count, total_duration, total_duration / 3600))

    count = 0
    for i in range(len(exp_list)):
        for j in range(exp_list[i].TOTAL_ROUNDS):
            count += 1
            exp_id = "{}-{}".format(exp_list[i].EXPERIMENT_ID, j)
            logger.info("running {}, ({}/{})".format(exp_id, count, total_count))

            if VIDEO:
                container = create_ffmpeg_container(exp_id)

            if exp_list[i].EMULATION:
                if exp_list[i].EMULATION_PROFILE != "":
                    # create nginx with trace
                    nginx_container = create_nginx_with_trace(exp_list[i].EMULATION_PROFILE)
                else:
                    restart_nginx()

            run_once(exp_id, exp_list[i])

            if VIDEO:
                container.stop()
                container.remove()

            if exp_list[i].EMULATION and exp_list[i].EMULATION_PROFILE != "":
                    nginx_container.remove(force=True)

    logger.info("Video Streaming completed.")
