import bank_services
import getpass # 비밀번호를 안전하게 입력받기 위함

def show_main_menu():
    print("\n===== 메인 메뉴 =====")
    print("1. 회원가입")
    print("2. 로그인")
    print("3. 종료")
    return input("메뉴를 선택하세요: ")

def show_bank_menu():
    print("\n===== 은행 메뉴 =====")
    print("1. 내 계좌 생성")
    print("2. 내 계좌 조회")
    print("3. 입금")
    print("4. 출금")
    print("5. 계좌이체")
    print("6. 거래내역 조회")
    print("7. 로그아웃")
    return input("메뉴를 선택하세요: ")

def handle_main_menu():
    while True:
        choice = show_main_menu()
        if choice == '1':
            # 회원가입 처리
            username = input("사용자 ID: ")
            password = getpass.getpass("비밀번호: ")
            name = input("이름: ")
            if bank_services.register_user(username, password, name):
                print("회원가입이 완료되었습니다.")
            else:
                print("회원가입에 실패했습니다.")
        elif choice == '2':
            # 로그인 처리
            username = input("사용자 ID: ")
            password = getpass.getpass("비밀번호: ")
            user_info = bank_services.login_user(username, password)
            if user_info:
                print(f"\n{user_info['name']}님, 환영합니다.")
                handle_bank_menu(user_info) # 로그인 성공 시 은행 메뉴로
            else:
                print("로그인에 실패했습니다. ID 또는 비밀번호를 확인하세요.")
        elif choice == '3':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 다시 입력해주세요.")

def handle_bank_menu(user_info):
    while True:
        choice = show_bank_menu()
        if choice == '1':
            new_account = bank_services.create_account(user_info)
            if new_account:
                print(f"\n계좌가 성공적으로 생성되었습니다. 계좌번호: {new_account}")
            else:
                print("\n계좌 생성에 실패했습니다. 다시 시도해주세요.")
        elif choice == '2':
            my_accounts = bank_services.get_my_accounts(user_info)
            if not my_accounts: # 리스트가 비어있는 경우
                print("\n보유하신 계좌가 없습니다. 먼저 계좌를 생성해주세요.")
            else:
                print(f"\n--- {user_info['name']}님의 계좌 목록 ---")
                for acc in my_accounts:
                    # 통화 형식(,)과 날짜 형식을 보기 좋게 변경하여 출력
                    balance_formatted = f"{acc['balance']:,}" 
                    created_date = acc['created_at'].strftime('%Y-%m-%d')
                    print(f"계좌번호: {acc['account_no']}, 잔액: {balance_formatted}원, 개설일: {created_date}")
                print("--------------------------")
        elif choice == '3':
            # 입금 처리
            account_no = input("입금할 계좌번호를 입력하세요: ")
            
            try:
                amount_str = input("입금할 금액을 입력하세요: ")
                amount = int(amount_str)
            except ValueError:
                print("\n잘못된 금액입니다. 숫자만 입력해주세요.")
                continue # 메뉴로 다시 돌아감

            new_balance = bank_services.deposit(account_no, amount)
            if new_balance is not None:
                print(f"\n입금이 완료되었습니다. 계좌 '{account_no}'의 현재 잔액은 {new_balance:,}원입니다.")
            else:
                print("\n입금에 실패했습니다. 계좌번호나 금액을 다시 확인해주세요.")
        elif choice == '4':
            # 출금 처리
            account_no = input("출금할 계좌번호를 입력하세요: ")
            
            try:
                amount_str = input("출금할 금액을 입력하세요: ")
                amount = int(amount_str)
            except ValueError:
                print("\n잘못된 금액입니다. 숫자만 입력해주세요.")
                continue # 메뉴로 다시 돌아감

            new_balance = bank_services.withdraw(account_no, amount)
            if new_balance is not None:
                print(f"\n출금이 완료되었습니다. 계좌 '{account_no}'의 현재 잔액은 {new_balance:,}원입니다.")
            else:
                # 실패 메시지는 bank_services.withdraw에서 이미 출력했으므로 여기서는 추가 출력 안함
                print("\n출금에 실패했습니다. 계좌번호, 금액, 잔액을 다시 확인해주세요.")
        elif choice == '5':
            # 계좌이체 처리
            from_account_no = input(f"돈을 보낼 계좌번호를 입력하세요 (현재 로그인 사용자: {user_info['user_id']}): ")
            to_account_no = input("돈을 받을 계좌번호를 입력하세요: ")
            
            try:
                amount_str = input("이체할 금액을 입력하세요: ")
                amount = int(amount_str)
            except ValueError:
                print("\n잘못된 금액입니다. 숫자만 입력해주세요.")
                continue

            new_balance = bank_services.transfer(user_info['user_id'], from_account_no, to_account_no, amount)
            if new_balance is not None:
                print(f"\n계좌이체가 완료되었습니다. 출금 계좌 '{from_account_no}'의 현재 잔액은 {new_balance:,}원입니다.")
            else:
                print("\n계좌이체에 실패했습니다. 계좌번호, 금액, 잔액을 다시 확인해주세요.")
        elif choice == '6':
            # 거래내역 조회 처리
            account_no = input("거래 내역을 조회할 계좌번호를 입력하세요: ")
            transactions = bank_services.get_transaction_history(account_no)

            if not transactions:
                print(f"\n계좌 '{account_no}'의 거래 내역이 없거나, 계좌번호가 유효하지 않습니다.")
            else:
                print(f"\n--- 계좌 '{account_no}'의 거래 내역 ---")
                for tx in transactions:
                    tx_date_formatted = tx['tx_date'].strftime('%Y-%m-%d %H:%M:%S')
                    amount_formatted = f"{tx['amount']:,}"
                    target_info = ""
                    if tx['tx_type'] == '이체출금':
                        target_info = f" -> {tx['target_account']}"
                    elif tx['tx_type'] == '이체입금':
                        target_info = f" <- {tx['target_account']}"
                    print(f"[{tx_date_formatted}] {tx['tx_type']}: {amount_formatted}원 {target_info}")
                print("------------------------------------")

        elif choice == '7':
            print("로그아웃합니다.")
            break
        else:
            print("잘못된 선택입니다. 다시 입력해주세요.")

if __name__ == "__main__":
    handle_main_menu()
