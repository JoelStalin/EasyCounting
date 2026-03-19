# QA Case Matrix - 2026-03-18

Status legend:

- `P`: passed
- `PP`: partially passed
- `NE`: not executed
- `B`: blocked

## Portal case pack

- `TC01` protected-route redirect to login
- `TC02` successful login and route restore
- `TC03` auth shell renders user identity
- `TC04` admin create company
- `TC05` admin open company detail
- `TC06` client submit simulated e-CF
- `TC07` client profile navigation
- `TC08` logout returns to login

## Execution map

- `admin-portal`: `TC01=P` `TC02=P` `TC03=P` `TC04=P` `TC05=P` `TC06=NE` `TC07=NE` `TC08=NE`
- `client-portal`: `TC01=P` `TC02=P` `TC03=P` `TC04=NE` `TC05=NE` `TC06=P` `TC07=P` `TC08=P`

## Notes

- The suite currently prioritizes stable, high-signal flows over broad route enumeration.
- Deep admin tabs such as accounting, plans and settings remain candidates for future API-backed Selenium cases.
