from .. import db
from ..core import local_path
from .score import parse_score, xml_bytes


def save_score(piece_id, root, source):
    parse_score(root)  # Reject empty or invalid engine output before creating a version.
    identity = db.uid()
    path = f"musicxml/{piece_id}/{identity}.musicxml"
    destination = local_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(xml_bytes(root))
    try:
        with db.connection() as con:
            sequence = con.execute(
                "SELECT coalesce(max(sequence),0)+1 FROM score_versions WHERE piece_id=?", (piece_id,)
            ).fetchone()[0]
            con.execute(
                "INSERT INTO score_versions VALUES (?,?,?,?,?,?)",
                (identity, piece_id, sequence, path, source, db.now()),
            )
            con.execute(
                "UPDATE pieces SET current_version=?,updated_at=? WHERE id=?", (identity, db.now(), piece_id)
            )
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return identity
