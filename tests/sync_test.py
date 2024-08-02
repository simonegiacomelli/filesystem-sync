import shutil

import pytest

from tests.sync_fixture import SyncFixture

invalid_utf8 = b'\x80\x81\x82'


@pytest.fixture
def target(tmp_path):
    fixture = SyncFixture(tmp_path)
    yield fixture
    fixture.debounced_watcher.stop()
    fixture.debounced_watcher.join()


def test_new_file(target):
    # GIVEN
    target.start()
    (target.source / 'new_file.txt').write_text('new file')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert (target.target / 'new_file.txt').exists()
    assert (target.target / 'new_file.txt').read_text() == 'new file'


def test_new_file__optimize(target):
    # GIVEN
    target.start()
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    target.wait_at_rest()

    # WHEN
    changes = target.do_sync()

    # THEN
    assert (target.target / 'new_file.txt').exists()
    assert (target.target / 'new_file.txt').read_text() == 'new file2'
    assert len(changes) == 1


def test_new_file_and_delete(target):
    # GIVEN
    target.start()
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    (target.source / 'new_file.txt').unlink()
    target.wait_at_rest()

    # WHEN
    changes = target.get_changes()

    # THEN
    assert changes == []


def test_new_file_in_subfolder(target):
    # GIVEN
    target.start()
    sub1 = target.source / 'sub1'
    sub1.mkdir()
    (sub1 / 'foo.txt').write_text('sub-file')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert (target.target / 'sub1/foo.txt').exists()
    assert (target.target / 'sub1/foo.txt').read_text() == 'sub-file'


def test_delete_file(target):
    # GIVEN
    source_foo = target.source / 'foo.txt'
    source_foo.write_text('content1')
    target_foo = target.target / 'foo.txt'
    target_foo.write_text('content1')
    target.start()

    source_foo.unlink()
    target.wait_at_rest()

    # WHEN
    changes = target.do_sync()

    # THEN
    assert not target_foo.exists()
    assert len(changes) == 1


def test_created(target):
    # GIVEN
    target.start()
    (target.source / 'foo.txt').touch()
    target.wait_at_rest()

    # WHEN
    changes = target.do_sync()

    # THEN
    assert (target.target / 'foo.txt').exists()
    assert (target.target / 'foo.txt').stat().st_size == 0
    assert len(changes) == 1


def test_init(target):
    # GIVEN
    (target.source / 'foo.txt').write_text('c1')
    (target.source / 'foo.bin').write_bytes(invalid_utf8)

    # WHEN
    target.do_init()

    # THEN
    assert (target.target / 'foo.txt').read_text() == 'c1'
    assert (target.target / 'foo.bin').read_bytes() == invalid_utf8
    assert target.synchronized(), target.sync_error()


def test_synchronized_no_files(target):
    # GIVEN

    # WHEN
    target.do_init()

    # THEN
    assert target.synchronized()
    assert target.sync_error() is None


def test_synchronized_some_files(target):
    # GIVEN
    (target.source / 'foo.txt').write_text('c1')

    assert target.synchronized() is False
    assert target.sync_error() is not None


def test_delete_folder(target):
    # GIVEN
    (target.source / 'sub1').mkdir()
    (target.source / 'sub1/foo.txt').write_text('content1')
    target.copy_source_to_target()
    target.start()

    shutil.rmtree(target.source / 'sub1')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert target.synchronized(), target.sync_error()


def test_delete_folder__and_recreate_it(target):
    def build():
        (target.source / 'sub1').mkdir()
        (target.source / 'sub1/foo.txt').write_text('content1')

    # GIVEN
    build()
    target.copy_source_to_target()
    target.start()

    # WHEN
    shutil.rmtree(target.source / 'sub1')
    build()
    target.wait_at_rest()

    target.do_sync()

    # THEN
    assert target.synchronized(), target.sync_error()


def test_invalid_text(target):
    # GIVEN
    target.start()

    (target.source / 'foo.bin').write_bytes(invalid_utf8)
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert target.synchronized(), target.sync_error()
    assert (target.target / 'foo.bin').read_bytes() == invalid_utf8
