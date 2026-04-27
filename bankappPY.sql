

-- 1. 회원(USERS) 테이블: 회원가입 및 로그인, 권한 관리
CREATE TABLE USERS (
    USER_ID VARCHAR2(50) PRIMARY KEY,       -- 아이디 (기본키)
    PASSWORD VARCHAR2(100) NOT NULL,        -- 비밀번호 (필수)
    USER_NAME VARCHAR2(50) NOT NULL,        -- 이름 (필수)
    -- 권한 컬럼: 기본값은 'USER'이며, 'USER' 또는 'ADMIN'만 입력되도록 CHECK 제약조건 설정
    ROLE VARCHAR2(10) DEFAULT 'USER' CONSTRAINT check_role CHECK(ROLE IN ('USER', 'ADMIN')), 
    CREATED_AT DATE DEFAULT SYSDATE         -- 가입일자 (기본값 현재 날짜)
);

-- 2. 계좌(ACCOUNTS) 테이블: 내 계좌 생성 및 조회, 잔액 관리
CREATE TABLE ACCOUNTS (
    ACCOUNT_NO VARCHAR2(50) PRIMARY KEY,    -- 계좌번호 (기본키)
    USER_ID VARCHAR2(50),                   -- 소유주 아이디 (외래키)
    BALANCE NUMBER DEFAULT 0,               -- 잔액 (기본값 0)
    CREATED_AT DATE DEFAULT SYSDATE,        -- 계좌생성일자 (기본값 현재 날짜)
    CONSTRAINT account_user_fk FOREIGN KEY (USER_ID) REFERENCES USERS (USER_ID) -- 외래키 설정
);

-- 3. 거래내역(TRANSACTIONS) 테이블: 입금, 출금, 계좌이체 및 거래내역 조회
CREATE TABLE TRANSACTIONS (
    TX_ID NUMBER PRIMARY KEY,               -- 거래 고유 ID (기본키)
    ACCOUNT_NO VARCHAR2(50),                -- 거래 발생 계좌 (외래키)
    TX_TYPE VARCHAR2(20) NOT NULL,          -- 거래 유형 ('입금', '출금', '이체')
    AMOUNT NUMBER NOT NULL,                 -- 거래 금액
    TARGET_ACCOUNT VARCHAR2(50),            -- 이체 시 대상 계좌번호 (입출금 시에는 NULL)
    TX_DATE DATE DEFAULT SYSDATE,           -- 거래일시 (기본값 현재 날짜)
    CONSTRAINT tx_account_fk FOREIGN KEY (ACCOUNT_NO) REFERENCES ACCOUNTS (ACCOUNT_NO) -- 외래키 설정
);

-- (참고: 외부 지식) 거래내역 ID 자동 증가를 위한 시퀀스 생성
CREATE SEQUENCE TX_SEQ START WITH 1 INCREMENT BY 1;