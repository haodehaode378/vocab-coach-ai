# AI Agent 记单词项目｜06 数据库设计与 Prisma Schema（初稿）

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())
}

model VocabItem {
  id           String   @id @default(cuid())
  userId       String
  word         String
  phonetic     String?
  meaningZh    String?
  example      String?
  tags         String?
  easeFactor   Float    @default(2.5)
  intervalDays Int      @default(0)
  repetitions  Int      @default(0)
  nextReviewAt DateTime?
  createdAt    DateTime @default(now())

  @@index([userId, nextReviewAt])
  @@unique([userId, word])
}
```
