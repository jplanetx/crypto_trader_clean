import json

def verify_paper_trading_config():
    try:
        with open("config/config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found.")
        return False

    if not config.get("paper_trading"):
        print("Error: paper_trading is not set to true.")
        return False

    risk_management = config.get("risk_management")
    if not risk_management:
        print("Error: risk_management section not found.")
        return False

    if risk_management.get("max_position_size") != 1:
        print("Error: max_position_size is not set to 1.")
        return False

    if risk_management.get("stop_loss_pct") != 2:
        print("Error: stop_loss_pct is not set to 2.")
        return False

    if risk_management.get("max_daily_loss") != 500:
        print("Error: max_daily_loss is not set to 500.")
        return False

    if risk_management.get("max_open_orders") != 2:
        print("Error: max_open_orders is not set to 2.")
        return False

    logging_config = config.get("logging")
    if not logging_config:
        print("Error: logging section not found.")
        return False

    if logging_config.get("level") != "DEBUG":
        print("Error: logging level is not set to DEBUG.")
        return False

    print("Paper trading configuration is valid.")
    return True

if __name__ == "__main__":
    verify_paper_trading_config()