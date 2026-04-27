import db_manager
import oracledb
import random

def register_user(username, password, name):
    """사용자 비밀번호"""
    conn = None
    try:
        conn = db_manager.get_connection()
        if not conn:
            return False
        
        with conn.cursor() as cursor:
            # SQL 테이블 컬럼명(USER_ID, PASSWORD, USER_NAME)에 맞게 작성
            sql = "INSERT INTO USERS (USER_ID, PASSWORD, USER_NAME) VALUES (:1, :2, :3)"
            cursor.execute(sql, [username, password, name])
            conn.commit()
            return True
    except oracledb.IntegrityError:
        # USER_ID가 Primary Key이므로, 중복된 ID로 가입 시도 시 이 에러가 발생합니다.
        print(f"오류: 사용자 ID '{username}'가(이) 이미 존재합니다.")
        return False
    except oracledb.DatabaseError as e:
        print(f"데이터베이스 오류가 발생했습니다: {e}")
        if conn:
            conn.rollback() # 오류 발생 시 롤백
        return False
    finally:
        if conn:
            conn.close() # 사용한 연결은 반드시 닫아줍니다.

def login_user(username, password):
    # 사용자 로그인
    conn = None
    try:
        conn = db_manager.get_connection()
        if not conn:
            return None

        with conn.cursor() as cursor:
            # 로그인 성공 시 필요한 정보(USER_ID, USER_NAME)를 함께 조회
            sql = "SELECT USER_ID, USER_NAME, PASSWORD FROM USERS WHERE USER_ID = :1"
            cursor.execute(sql, [username])
            result = cursor.fetchone()

            if result:
                user_id, user_name, db_password = result
                # 사용자 입력 비밀번호와 DB에 저장된 비밀번호를 직접 비교
                if password == db_password:
                    return {'user_id': user_id, 'name': user_name}
        
        # 사용자가 없거나 비밀번호가 틀린 경우
        return None
    except oracledb.DatabaseError as e:
        print(f"데이터베이스 오류가 발생했습니다: {e}")
        return None
    finally:
        if conn:
            conn.close()

def create_account(user_info):
    """계좌 생성 로직. '3333-XXXX-XXXX' 형식의 계좌번호를 생성하여 DB에 저장합니다."""
    # 1. 계좌번호 생성 (예: '3333-' + 8자리 난수)
    new_account_no = f"3333-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    user_id = user_info['user_id']

    conn = None
    try:
        conn = db_manager.get_connection()
        if not conn:
            print("DB 연결에 실패하여 계좌를 생성할 수 없습니다.")
            return None

        with conn.cursor() as cursor:
            sql = "INSERT INTO ACCOUNTS (ACCOUNT_NO, USER_ID) VALUES (:1, :2)"
            cursor.execute(sql, [new_account_no, user_id])
            conn.commit()
            return new_account_no # 성공 시 생성된 계좌번호 반환
    except oracledb.DatabaseError as e:
        print(f"계좌 생성 중 데이터베이스 오류가 발생했습니다: {e}")
        if conn:
            conn.rollback()
        return None # 실패 시 None 반환
    finally:
        if conn:
            conn.close()

def get_my_accounts(user_info):
    """내 계좌 조회 로직. 사용자의 모든 계좌 정보를 조회하여 리스트로 반환합니다."""
    user_id = user_info['user_id']
    conn = None
    accounts = [] # 결과를 담을 리스트

    try:
        conn = db_manager.get_connection()
        if not conn:
            print("DB 연결에 실패하여 계좌를 조회할 수 없습니다.")
            return [] # 빈 리스트 반환

        with conn.cursor() as cursor:
            # ACCOUNTS 테이블에서 USER_ID가 일치하는 모든 계좌의 정보를 조회 (생성일 순 정렬)
            sql = "SELECT ACCOUNT_NO, BALANCE, CREATED_AT FROM ACCOUNTS WHERE USER_ID = :1 ORDER BY CREATED_AT"
            cursor.execute(sql, [user_id])
            
            # 조회된 모든 결과를 딕셔너리 리스트로 변환
            for row in cursor.fetchall():
                accounts.append({'account_no': row[0], 'balance': row[1], 'created_at': row[2]})
        
        return accounts
    except oracledb.DatabaseError as e:
        print(f"계좌 조회 중 데이터베이스 오류가 발생했습니다: {e}")
        return [] # 오류 발생 시 빈 리스트 반환
    finally:
        if conn:
            conn.close()

def deposit(account_no, amount):
    """
    지정된 계좌에 금액을 입금하고 거래 내역을 기록합니다.
    ACCOUNTS 테이블의 잔액을 업데이트하고, TRANSACTIONS 테이블에 '입금' 내역을 추가합니다.
    이 두 작업은 하나의 트랜잭션으로 처리됩니다.

    Args:
        account_no (str): 입금할 계좌번호
        amount (int): 입금할 금액

    Returns:
        int: 입금 후 새로운 잔액. 실패 시 None.
    """
    if amount <= 0:
        print("오류: 입금 금액은 0보다 커야 합니다.")
        return None

    conn = None
    try:
        conn = db_manager.get_connection()
        if not conn:
            return None

        with conn.cursor() as cursor:
            # 1. 계좌 잔액 업데이트
            update_sql = "UPDATE ACCOUNTS SET BALANCE = BALANCE + :1 WHERE ACCOUNT_NO = :2"
            cursor.execute(update_sql, [amount, account_no])

            # 업데이트된 행이 없으면(rowcount == 0) 계좌가 존재하지 않는 것임
            if cursor.rowcount == 0:
                print(f"오류: 계좌번호 '{account_no}'를 찾을 수 없습니다.")
                conn.rollback() # 작업을 되돌림
                return None

            # 2. 거래 내역(TRANSACTION) 기록 (시퀀스 사용)
            insert_tx_sql = """
                INSERT INTO TRANSACTIONS (TX_ID, ACCOUNT_NO, TX_TYPE, AMOUNT)
                VALUES (TX_SEQ.NEXTVAL, :1, '입금', :2)
            """
            cursor.execute(insert_tx_sql, [account_no, amount])

            # 3. 모든 작업이 성공했으므로 트랜잭션 커밋
            conn.commit()

            # 4. 최종 잔액을 조회하여 반환
            cursor.execute("SELECT BALANCE FROM ACCOUNTS WHERE ACCOUNT_NO = :1", [account_no])
            new_balance = cursor.fetchone()[0]
            return new_balance
    except oracledb.DatabaseError as e:
        print(f"입금 처리 중 데이터베이스 오류가 발생했습니다: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def withdraw(account_no, amount):
    """
    지정된 계좌에서 금액을 출금하고 거래 내역을 기록합니다.
    ACCOUNTS 테이블의 잔액을 업데이트하고, TRANSACTIONS 테이블에 '출금' 내역을 추가합니다.
    잔액 부족 시 출금을 허용하지 않습니다. 이 두 작업은 하나의 트랜잭션으로 처리됩니다.

    Args:
        account_no (str): 출금할 계좌번호
        amount (int): 출금할 금액

    Returns:
        int: 출금 후 새로운 잔액. 실패 시 None.
    """
    if amount <= 0:
        print("오류: 출금 금액은 0보다 커야 합니다.")
        return None

    conn = None
    try:
        conn = db_manager.get_connection()
        if not conn:
            return None

        with conn.cursor() as cursor:
            # 1. 현재 잔액 조회 및 계좌 존재 여부 확인
            cursor.execute("SELECT BALANCE FROM ACCOUNTS WHERE ACCOUNT_NO = :1 FOR UPDATE", [account_no])
            # FOR UPDATE는 동시성 문제를 방지하기 위해 해당 행에 락을 걸어 다른 트랜잭션이 수정하지 못하게 합니다.
            result = cursor.fetchone()

            if not result:
                print(f"오류: 계좌번호 '{account_no}'를 찾을 수 없습니다.")
                conn.rollback()
                return None

            current_balance = result[0]

            # 2. 잔액 부족 여부 확인
            if current_balance < amount:
                print(f"오류: 잔액이 부족합니다. 현재 잔액: {current_balance:,}원, 출금 요청 금액: {amount:,}원")
                conn.rollback() # 잔액 부족으로 인한 실패이므로 롤백
                return None

            # 3. 계좌 잔액 업데이트
            update_sql = "UPDATE ACCOUNTS SET BALANCE = BALANCE - :1 WHERE ACCOUNT_NO = :2"
            cursor.execute(update_sql, [amount, account_no])

            # 4. 거래 내역(TRANSACTION) 기록 (시퀀스 사용)
            insert_tx_sql = """
                INSERT INTO TRANSACTIONS (TX_ID, ACCOUNT_NO, TX_TYPE, AMOUNT)
                VALUES (TX_SEQ.NEXTVAL, :1, '출금', :2)
            """
            cursor.execute(insert_tx_sql, [account_no, amount])

            # 5. 모든 작업이 성공했으므로 트랜잭션 커밋
            conn.commit()

            # 6. 최종 잔액을 조회하여 반환
            new_balance = current_balance - amount # 이미 잔액을 알고 있으므로 다시 조회할 필요 없음
            return new_balance
    except oracledb.DatabaseError as e:
        print(f"출금 처리 중 데이터베이스 오류가 발생했습니다: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def transfer(user_id, from_account_no, to_account_no, amount):
    """
    한 계좌에서 다른 계좌로 금액을 이체합니다.
    송금 계좌가 현재 로그인한 사용자의 소유인지 확인하고,
    송금 계좌와 수취 계좌가 모두 유효해야 하며, 송금 계좌의 잔액이 충분해야 합니다.
    이 모든 과정은 하나의 트랜잭션으로 처리됩니다.

    Args:
        user_id (str): 현재 로그인한 사용자의 ID (송금 계좌 소유주 확인용)
        from_account_no (str): 돈을 보내는 계좌번호
        to_account_no (str): 돈을 받는 계좌번호
        amount (int): 이체할 금액

    Returns:
        int: 이체 후 송금 계좌의 새로운 잔액. 실패 시 None.
    """
    if amount <= 0:
        print("오류: 이체 금액은 0보다 커야 합니다.")
        return None
    
    if from_account_no == to_account_no:
        print("오류: 동일한 계좌로 이체할 수 없습니다.")
        return None

    conn = None
    try:
        conn = db_manager.get_connection()
        if not conn:
            return None

        with conn.cursor() as cursor:
            # 1. 송금 계좌의 소유주, 잔액 확인 및 락(Lock)
            # USER_ID와 BALANCE를 함께 조회하여 소유주 확인 및 잔액 확인을 한 번에 처리
            cursor.execute("SELECT USER_ID, BALANCE FROM ACCOUNTS WHERE ACCOUNT_NO = :1 FOR UPDATE", [from_account_no])
            from_account_info = cursor.fetchone()

            if not from_account_info:
                print(f"오류: 보내는 분의 계좌번호 '{from_account_no}'를 찾을 수 없습니다.")
                conn.rollback()
                return None

            owner_id, from_balance = from_account_info

            # 1a. 송금 계좌 소유주 확인
            if owner_id != user_id:
                print(f"오류: 계좌 '{from_account_no}'는 현재 로그인한 사용자({user_id})의 소유가 아닙니다.")
                conn.rollback()
                return None

            # 1b. 잔액 부족 여부 확인
            if from_balance < amount:
                print(f"오류: 잔액이 부족합니다. 현재 잔액: {from_balance:,}원")
                conn.rollback()
                return None

            # 2. 수취 계좌 존재 여부 확인
            cursor.execute("SELECT 1 FROM ACCOUNTS WHERE ACCOUNT_NO = :1", [to_account_no])
            if not cursor.fetchone():
                print(f"오류: 받는 분의 계좌번호 '{to_account_no}'를 찾을 수 없습니다.")
                conn.rollback()
                return None

            # 3. 송금 계좌에서 금액 차감 & 수취 계좌에 금액 추가
            cursor.execute("UPDATE ACCOUNTS SET BALANCE = BALANCE - :1 WHERE ACCOUNT_NO = :2", [amount, from_account_no])
            cursor.execute("UPDATE ACCOUNTS SET BALANCE = BALANCE + :1 WHERE ACCOUNT_NO = :2", [amount, to_account_no])

            # 4. 거래 내역 기록 (송금자: '이체출금', 수취자: '이체입금')
            tx_sql = "INSERT INTO TRANSACTIONS (TX_ID, ACCOUNT_NO, TX_TYPE, AMOUNT, TARGET_ACCOUNT) VALUES (TX_SEQ.NEXTVAL, :1, :2, :3, :4)"
            cursor.execute(tx_sql, [from_account_no, '이체출금', amount, to_account_no])
            cursor.execute(tx_sql, [to_account_no, '이체입금', amount, from_account_no])

            # 5. 모든 작업이 성공했으므로 트랜잭션 커밋
            conn.commit()

            return from_balance - amount
    except oracledb.DatabaseError as e:
        print(f"계좌이체 처리 중 데이터베이스 오류가 발생했습니다: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def get_transaction_history(account_no):
    """
    특정 계좌의 모든 거래 내역을 조회합니다.

    Args:
        account_no (str): 거래 내역을 조회할 계좌번호

    Returns:
        list: 거래 내역 딕셔너리 리스트. 각 딕셔너리는 'tx_id', 'account_no', 'tx_type', 'amount', 'target_account', 'tx_date' 키를 가집니다.
              계좌가 없거나 오류 발생 시 빈 리스트 반환.
    """
    conn = None
    transactions = []
    try:
        conn = db_manager.get_connection()
        if not conn:
            print("DB 연결에 실패하여 거래 내역을 조회할 수 없습니다.")
            return []

        with conn.cursor() as cursor:
            # 1. 계좌 존재 여부 확인
            cursor.execute("SELECT 1 FROM ACCOUNTS WHERE ACCOUNT_NO = :1", [account_no])
            if not cursor.fetchone():
                print(f"오류: 계좌번호 '{account_no}'를 찾을 수 없습니다.")
                return []

            # 2. 거래 내역 조회 (최신순으로 정렬)
            sql = """
                SELECT TX_ID, ACCOUNT_NO, TX_TYPE, AMOUNT, TARGET_ACCOUNT, TX_DATE
                FROM TRANSACTIONS
                WHERE ACCOUNT_NO = :1
                ORDER BY TX_DATE DESC, TX_ID DESC
            """
            cursor.execute(sql, [account_no])

            for row in cursor.fetchall():
                transactions.append({
                    'tx_id': row[0],
                    'account_no': row[1],
                    'tx_type': row[2],
                    'amount': row[3],
                    'target_account': row[4], # 이체 시 대상 계좌번호, 입출금 시 NULL
                    'tx_date': row[5]
                })
        return transactions
    except oracledb.DatabaseError as e:
        print(f"거래 내역 조회 중 데이터베이스 오류가 발생했습니다: {e}")
        return []
    finally:
        if conn:
            conn.close()
