import Link from "next/link";

export default function NotFound() {
  return (
    <section className="empty-state">
      <p className="eyebrow">404 / NOT FOUND</p>
      <h1>没有找到这个对话</h1>
      <p>对话可能已被删除，或者链接中的 ID 不正确。</p>
      <Link className="primary-button" href="/conversations">
        返回对话列表
      </Link>
    </section>
  );
}
